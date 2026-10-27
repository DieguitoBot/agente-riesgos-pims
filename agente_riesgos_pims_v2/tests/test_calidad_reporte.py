import copy
import json
import unittest
from unittest.mock import patch

from knowledge.evidencia_rag import validar_citas_rag
from llm.ollama_client import analizar_con_ollama, OllamaError, validar_analisis, validar_vinculos_documentales
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

    def test_contrato_acepta_reportes_sin_cupos_de_contenido(self):
        analisis = copy.deepcopy(ANALISIS)
        for campo in ('riesgos_identificados', 'indicadores_riesgo', 'referencias_iso',
                      'referencias_ley', 'referencias_rag'):
            esquema = ESQUEMA_ANALISIS['properties'][campo]
            self.assertNotIn('maxItems', esquema)
            plantilla = {k: ('alta' if k == 'prioridad' else 'Contenido verificable')
                         for k in esquema['items']['properties']}
            analisis[campo] = [dict(plantilla, riesgo=f'Riesgo {i}') for i in range(101)]
        validado = validar_analisis(analisis)
        for campo in ('riesgos_identificados', 'indicadores_riesgo', 'referencias_iso',
                      'referencias_ley', 'referencias_rag'):
            self.assertEqual(len(validado[campo]), 101)

    def test_presupuesto_configurable_y_truncamiento_no_publicable(self):
        with patch.dict('os.environ', {'OLLAMA_NUM_CTX': '40000', 'OLLAMA_NUM_PREDICT': '20000'}), \
                patch('llm.ollama_client._solicitar', return_value={
                    'done': True, 'done_reason': 'length',
                    'message': {'content': json.dumps(ANALISIS)}}) as pedir:
            with self.assertRaisesRegex(OllamaError, 'límite de generación'):
                analizar_con_ollama(self.contexto)
        self.assertEqual(pedir.call_count, 2)
        self.assertEqual(pedir.call_args.kwargs['json']['options']['num_predict'], 20000)
        self.assertEqual(pedir.call_args.kwargs['json']['options']['num_ctx'], 40000)

    def test_api_exporta_todos_los_riesgos_e_indicadores(self):
        analisis = copy.deepcopy(ANALISIS)
        analisis['riesgos_identificados'] = [
            dict(ANALISIS['riesgos_identificados'][0], riesgo=f'Riesgo {i}') for i in range(6)]
        analisis['indicadores_riesgo'] = [dict(
            riesgo=f'Riesgo {i}', indicador=f'Indicador {i}', evidencia='sin control de acceso',
            formula='accesos rechazados / accesos revisados * 100',
            fuente_datos='Registro de pruebas de acceso', frecuencia='Mensual propuesta',
            umbral_propuesto='100% propuesto') for i in range(6)]
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=analisis), \
                patch('rag.recuperar_contexto.recuperar_contexto_rag', return_value={
                    'estado': 'sin_indice', 'fragmentos': [], 'mensaje': 'Prueba'}):
            respuesta = app.test_client().post('/api/evaluar', json={
                'descripcion': self.contexto['descripcion'], 'probabilidad': 3,
                'impacto': 4, 'exigir_ia': True})
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertEqual(len(resultado['analisis_ia']['riesgos_identificados']), 6)
        self.assertEqual(len(resultado['indicadores_riesgo']), 6)
        self.assertIn('6. Riesgo 5', resultado['reporte_texto'])
        self.assertIn('Indicador 5', resultado['reporte_texto'])

    def test_citas_del_contrato_son_extractos_literales_acotados(self):
        contexto = copy.deepcopy(self.contexto)
        contexto['contexto_legal'] = {'fragmentos': [dict(
            articulo='9', texto='Artículo 9. Seguridad\n' + 'Contenido verificable de la fuente documental. ' * 10)]}
        esquema = construir_esquema(contexto)['properties']
        for campo, texto, maximo, clave in (
                ('referencias_rag', self.fuente['texto'], 240, 'cita'),
                ('referencias_ley', contexto['contexto_legal']['fragmentos'][0]['texto'], 160, 'cita_normativa')):
            citas = esquema[campo]['items']['anyOf'][0]['properties'][clave]['enum']
            self.assertTrue(citas)
            for cita in citas:
                self.assertTrue(20 <= len(cita) <= maximo)
                self.assertIn(cita, ' '.join(texto.split()))

    def test_contrato_vincula_cada_cita_con_su_fuente(self):
        contexto = copy.deepcopy(self.contexto)
        segunda = dict(self.fuente, id='F2', texto='La conservación requiere un plazo documentado para cada finalidad.')
        contexto['contexto_rag']['fragmentos'].append(segunda)
        opciones = construir_esquema(contexto)['properties']['referencias_rag']['items']['anyOf']
        self.assertEqual(len(opciones), 2)
        for opcion, fuente in zip(opciones, contexto['contexto_rag']['fragmentos']):
            campos = opcion['properties']
            self.assertEqual(campos['fuente_id']['enum'], [fuente['id']])
            for cita in campos['cita']['enum']:
                self.assertIn(cita, fuente['texto'])

    def test_cita_invalida_pide_reparacion_antes_de_publicar(self):
        analisis = copy.deepcopy(ANALISIS)
        analisis['referencias_rag'] = [dict(self.cita, cita='Una cita inexistente en esta fuente documental.')]
        with self.assertRaisesRegex(OllamaError, 'Referencia inválida'):
            validar_vinculos_documentales(analisis, self.contexto)
        analisis['referencias_rag'] = [self.cita]
        validar_vinculos_documentales(analisis, self.contexto)

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
        self.assertEqual(solicitud['options']['num_predict'], 16384)
        self.assertEqual(solicitud['options']['presence_penalty'], 0)

    def test_contrato_restringe_hechos_y_fuentes_sin_mutar_otras_solicitudes(self):
        esquema = construir_esquema(self.contexto)['properties']
        self.assertEqual(esquema['referencias_rag']['items']['anyOf'][0]['properties']['fuente_id']['enum'], ['F1'])
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
