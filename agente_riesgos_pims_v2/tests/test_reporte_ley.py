import copy
import json
import unittest
from unittest.mock import patch
import requests

from app import app
from knowledge.documento_ley import leer_articulos, recuperar_contexto_legal
from llm.ollama_client import analizar_con_ollama, OllamaError
from skills.evaluacion_riesgo import evaluar_riesgo
from tests.test_ollama_client import ANALISIS


class TestReporteLey(unittest.TestCase):
    def setUp(self):
        self.analisis = copy.deepcopy(ANALISIS)
        self.datos = dict(descripcion='La universidad almacena datos sin control de acceso.',
                          probabilidad=3, impacto=4)
        self.analisis['referencias_ley'] = [dict(riesgo='Acceso no autorizado', articulo='9',
            evidencia='sin control de acceso', motivo='Posible exposición por permisos no delimitados.',
            evidencia_requerida='Revisar permisos efectivos y matriz de roles.',
            cita_normativa='las medidas técnicas, organizativas y legales necesarias')]

    def test_ley_real_citas_trazabilidad_y_excepciones(self):
        articulos, huella = leer_articulos()
        self.assertEqual(len(huella), 64)
        self.assertIn('Principio de seguridad', articulos['9']['titulo'])
        self.assertNotIn('CONCORDANCIAS', articulos['9']['texto'])
        d = recuperar_contexto_legal('Tratamiento sin consentimiento')
        self.assertTrue({'5', '14'} <= {f['articulo'] for f in d['fragmentos']})
        self.assertIn('2013', d['mensaje'])

    def test_reporte_ia_con_ley_verificada_y_modelo_por_solicitud(self):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=self.analisis) as llm:
            r = evaluar_riesgo(**self.datos, modelo='otro:7b')
        self.assertEqual(r['modelo'], 'otro:7b')
        self.assertEqual(llm.call_args.args[0]['modelo_solicitado'], 'otro:7b')
        self.assertTrue(llm.call_args.args[0]['contexto_legal']['fragmentos'])
        self.assertTrue(r['reporte_ia_generado'])
        self.assertEqual(r['referencias_ley'][0]['articulo'], '9')
        self.assertIn('Artículo 9', r['reporte_texto'])
        self.assertIn('Definir roles de acceso', r['reporte_texto'])
        self.assertIn('SHA256', r['reporte_texto'])

    def test_cita_articulo_y_hecho_inventados_no_llegan_al_reporte(self):
        for campo, valor in [('cita_normativa', 'la ley exige cifrado de 999 bits'),
                             ('articulo', '999'), ('evidencia', 'se filtraron mil registros'),
                             ('riesgo', 'Riesgo inventado')]:
            a = copy.deepcopy(self.analisis)
            a['referencias_ley'][0][campo] = valor
            with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=a):
                r = evaluar_riesgo(**self.datos)
            self.assertEqual(r['referencias_ley'], [])
            self.assertEqual(r['analisis_ia']['referencias_ley'], [])
            self.assertNotIn(valor, r['reporte_texto'])

    def test_ia_obligatoria_devuelve_error_y_no_disfraza_reglas(self):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', side_effect=OllamaError('Timeout')):
            r = app.test_client().post('/api/evaluar', json=dict(self.datos, exigir_ia=True))
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json['codigo'], 'ia_no_disponible')
        self.assertFalse(r.json['resultado_preliminar']['reporte_ia_generado'])
        self.assertIn('REPORTE IA NO DISPONIBLE', r.json['resultado_preliminar']['reporte_texto'])

    def test_fuente_ley_y_modelo_invalido(self):
        cliente = app.test_client()
        with cliente.get('/api/fuente-ley/9') as r:
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.mimetype, 'text/plain')
            self.assertIn('Principio de seguridad', r.get_data(as_text=True))
        self.assertEqual(cliente.get('/api/fuente-ley/999').status_code, 404)
        with patch('skills.evaluacion_riesgo.analizar_con_ollama') as llm:
            for modelo in [[], 'modelo:cloud', '', 123]:
                self.assertEqual(cliente.post('/api/evaluar', json=dict(self.datos, modelo=modelo)).status_code, 400)
            llm.assert_not_called()

    def test_un_reintento_recupera_json_y_no_repite_timeouts(self):
        with patch('llm.ollama_client.requests.Session') as session:
            req = session.return_value.__enter__.return_value.request
            req.return_value.status_code = 200
            req.return_value.json.side_effect = [
                {'message': {'content': '{}'}},
                {'message': {'content': json.dumps(ANALISIS)}}]
            self.assertEqual(analizar_con_ollama({'descripcion': 'Datos sin control de acceso'}), ANALISIS)
            self.assertEqual(req.call_count, 2)
            self.assertIn('contrato', req.call_args.kwargs['json']['messages'][0]['content'])
        with patch('llm.ollama_client.requests.Session') as session:
            req = session.return_value.__enter__.return_value.request
            req.side_effect = requests.Timeout()
            with self.assertRaises(OllamaError):
                analizar_con_ollama({})
            self.assertEqual(req.call_count, 1)

    def test_dos_respuestas_invalidas_terminan_con_error_claro(self):
        with patch('llm.ollama_client.requests.Session') as session:
            req = session.return_value.__enter__.return_value.request
            req.return_value.status_code = 200
            req.return_value.json.return_value = {'message': {'content': '{}'}}
            with self.assertRaisesRegex(OllamaError, 'dos intentos'):
                analizar_con_ollama({})
            self.assertEqual(req.call_count, 2)

    def test_informe_breve_no_sustituye_el_reporte_completo(self):
        breve = dict(informe='La ausencia de roles expone los datos a consultas indebidas. Definir roles y probar el rechazo de accesos.',
                     riesgos=[dict(riesgo='Acceso no autorizado', evidencia='sin control de acceso', medida='Definir y probar roles de acceso.')])
        with patch('llm.ollama_client.requests.Session') as session:
            req = session.return_value.__enter__.return_value.request
            req.return_value.status_code = 200
            req.return_value.json.side_effect = [{'message': {'content': '{}'}},
                                                {'message': {'content': json.dumps(breve)}}]
            r = app.test_client().post('/api/evaluar', json=dict(self.datos, exigir_ia=True))
        self.assertEqual(r.status_code, 503)
        self.assertNotIn('reporte_texto', r.json)
        self.assertEqual(req.call_count, 2)

    def test_informe_breve_con_hechos_inventados_no_se_publica(self):
        breve = dict(informe='Hubo un incidente.', riesgos=[dict(riesgo='Acceso',
                     evidencia='se filtraron diez millones de datos', medida='Definir roles')])
        with patch('llm.ollama_client.requests.Session') as session:
            req = session.return_value.__enter__.return_value.request
            req.return_value.status_code = 200
            req.return_value.json.side_effect = [{'message': {'content': '{}'}},
                                                {'message': {'content': json.dumps(breve)}}]
            r = app.test_client().post('/api/evaluar', json=dict(self.datos, exigir_ia=True))
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.json['resultado_preliminar']['reporte_ia_generado'])
