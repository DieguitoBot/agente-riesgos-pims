import copy
import json
import unittest
from unittest.mock import patch

from knowledge.evidencia_rag import validar_citas_rag
from llm.ollama_client import analizar_con_ollama, OllamaError
from prompts.riesgo_prompt import construir_mensajes, construir_esquema, ESQUEMA_ANALISIS
from tests.test_ollama_client import ANALISIS
from skills.evaluacion_riesgo import _complementar
from app import app


class TestCalidadReporte(unittest.TestCase):
    def setUp(self):
        self.fuente = dict(id='F1', archivo='politica.md', pagina=None, fragmento=1,
                          texto='Los accesos a los registros deben limitarse a personas autorizadas para la finalidad.')
        self.contexto = dict(descripcion='Datos sin control de acceso',
                             contexto_rag={'fragmentos': [self.fuente]})
        self.analisis = copy.deepcopy(ANALISIS)
        self.cita = dict(riesgo='Acceso no autorizado', fuente_id='F1',
                         evidencia='sin control de acceso', cita=self.fuente['texto'],
                         aplicacion='Delimitar permisos sobre los registros; verificar la finalidad del acceso.')

    def test_cita_rag_conserva_procedencia(self):
        self.analisis['referencias_rag'] = [self.cita]
        refs, avisos = validar_citas_rag(self.analisis, self.contexto)
        self.assertEqual(refs[0]['archivo'], 'politica.md')
        self.assertEqual(refs[0]['cita'], self.fuente['texto'])
        self.assertFalse(avisos)

    def test_api_y_exportacion_conservan_solo_citas_rag_verificadas(self):
        self.analisis['referencias_rag'] = [self.cita, dict(self.cita,
            cita='Cita inventada que no debe aparecer en la salida.')]
        fuente = dict(self.fuente, similitud=.75)
        with patch('rag.recuperar_contexto.recuperar_contexto_rag', return_value={
                'estado': 'recuperado', 'fragmentos': [fuente], 'mensaje': 'Prueba'}), \
                patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=self.analisis):
            respuesta = app.test_client().post('/api/evaluar', json={
                'descripcion': self.contexto['descripcion'], 'probabilidad': 3,
                'impacto': 4, 'exigir_ia': True})
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertEqual(len(resultado['referencias_rag']), 1)
        self.assertEqual(resultado['analisis_ia']['referencias_rag'], resultado['referencias_rag'])
        self.assertIn(self.cita['aplicacion'], resultado['reporte_texto'])
        self.assertIn(self.fuente['texto'], resultado['reporte_texto'])
        self.assertIn('politica.md', resultado['reporte_texto'])
        self.assertNotIn('Cita inventada que no debe aparecer', json.dumps(resultado))

    def test_descarta_citas_o_hechos_inventados_y_fuente_inexistente(self):
        for cambio in [dict(cita='Una norma que el documento no contiene.'),
                       dict(fuente_id='F999'), dict(evidencia='se filtraron los datos'),
                       dict(riesgo='Otro riesgo'), dict(cita='Los accesos')]:
            with self.subTest(cambio=cambio):
                self.analisis['referencias_rag'] = [dict(self.cita, **cambio)]
                refs, avisos = validar_citas_rag(self.analisis, self.contexto)
                self.assertFalse(refs)
                self.assertTrue(avisos)

    def test_reintento_conserva_documentos_y_corrige_evidencia(self):
        inventado = copy.deepcopy(ANALISIS)
        inventado['riesgos_identificados'][0]['evidencia'] = 'Se filtraron 10000 registros'
        with patch('llm.ollama_client._solicitar') as pedir:
            pedir.side_effect = [
                {'message': {'content': json.dumps(inventado)}},
                {'message': {'content': json.dumps(ANALISIS)}},
            ]
            r = analizar_con_ollama(self.contexto)
        self.assertEqual(r, ANALISIS)
        mensajes = pedir.call_args.kwargs['json']['messages']
        self.assertIn('politica.md', mensajes[1]['content'])
        self.assertIn('literalmente', mensajes[-1]['content'])
        self.assertIn('riesgos_identificados', pedir.call_args.kwargs['json']['format']['properties'])

    def test_evidencia_inventada_no_se_publica(self):
        inventado = copy.deepcopy(ANALISIS)
        inventado['riesgos_identificados'][0]['evidencia'] = 'Se filtraron 10000 registros'
        with patch('llm.ollama_client._solicitar', return_value={
                'message': {'content': json.dumps(inventado)}}), self.assertRaisesRegex(
                    OllamaError, 'literalmente.*Se filtraron 10000 registros'):
            analizar_con_ollama(self.contexto)

    def test_prompt_conserva_fuentes_sin_duplicar_esquema(self):
        mensajes = construir_mensajes(self.contexto)
        self.assertIn('politica.md', mensajes[1]['content'])
        self.assertNotIn('additionalProperties', mensajes[0]['content'])
        datos = json.loads(mensajes[1]['content'].split('\n', 1)[1])
        self.assertEqual(datos['hechos_citables'], [self.contexto['descripcion']])
        self.assertNotIn('fragmento', datos['contexto_rag']['fragmentos'][0])

    def test_qwen_reciente_no_consume_salida_en_razonamiento(self):
        self.contexto['modelo_solicitado'] = 'qwen3.5:4b-q4_K_M'
        with patch('llm.ollama_client._solicitar', return_value={
                'message': {'content': json.dumps(ANALISIS)}}) as pedir:
            analizar_con_ollama(self.contexto)
        solicitud = pedir.call_args.kwargs['json']
        self.assertFalse(solicitud['think'])
        self.assertEqual(solicitud['options']['num_predict'], 3600)
        self.assertEqual(solicitud['options']['presence_penalty'], 0)

    def test_contrato_restringe_hechos_y_fuentes_sin_mutar_otras_solicitudes(self):
        esquema = construir_esquema(self.contexto)['properties']
        self.assertEqual(esquema['referencias_rag']['items']['properties']['fuente_id']['enum'], ['F1'])
        self.assertEqual(esquema['riesgos_identificados']['items']['properties']['evidencia']['enum'],
                         [self.contexto['descripcion']])
        self.assertEqual(esquema['referencias_iso']['maxItems'], 0)
        otro = construir_esquema({'descripcion': 'Otro caso sin fuentes.'})['properties']
        self.assertEqual(otro['referencias_rag']['maxItems'], 0)
        self.assertNotIn('enum', ESQUEMA_ANALISIS['properties']['riesgos_identificados']['items']['properties']['evidencia'])

    def test_descripcion_larga_sin_frases_no_impone_evidencia_ajena(self):
        descripcion = 'Texto continuo ' * 50
        esquema = construir_esquema({'descripcion': descripcion})['properties']
        self.assertNotIn('enum', esquema['riesgos_identificados']['items']['properties']['evidencia'])


    def test_indicador_con_aritmetica_arbitraria_se_descarta(self):
        self.contexto.update(rol_privacidad='responsable', puntaje=16, probabilidad=4, impacto=4)
        self.analisis['indicadores_riesgo'] = [dict(
            riesgo='Acceso no autorizado', evidencia='sin control de acceso',
            indicador='Exposición', formula='Exposición = (1 + 1) / 2',
            fuente_datos='Contexto de evaluación', frecuencia='Rara', umbral_propuesto='Sin incidentes')]
        r = _complementar(self.analisis, self.contexto, True)
        self.assertFalse(r['indicadores_riesgo'])
        self.assertTrue(any('variables observables' in a for a in r['avisos_revision']))
