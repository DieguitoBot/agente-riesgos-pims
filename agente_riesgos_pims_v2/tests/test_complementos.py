import copy
import json
import unittest
from unittest.mock import patch

from app import app
from llm.ollama_client import OllamaError, validar_analisis
from prompts.riesgo_prompt import construir_mensajes
from skills.evaluacion_riesgo import evaluar_riesgo
from tests.test_ollama_client import ANALISIS


class TestComplementos(unittest.TestCase):
    def setUp(self):
        self.analisis = copy.deepcopy(ANALISIS)
        self.descripcion = 'La universidad almacena DNI sin control de acceso y sin plazo de conservación.'
        self.referencia = dict(riesgo='Acceso no autorizado', control='A.3.9',
            evidencia='sin control de acceso', motivo='Posible acceso por personas sin autorización.',
            evidencia_requerida='Matriz de permisos y revisión de cuentas.',
            cita_normativa='Each profile comprises')
        self.analisis['referencias_iso'] = [self.referencia]
        self.analisis['indicadores_riesgo'] = [dict(riesgo='Acceso no autorizado',
            indicador='Cuentas con permisos excesivos', formula='Cuentas excesivas / cuentas revisadas × 100',
            evidencia='sin control de acceso', fuente_datos='Revisión de permisos',
            frecuencia='Mensual', umbral_propuesto='Mayor que 0 %, a validar por el equipo')]

    def evaluar(self, rol='responsable'):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=copy.deepcopy(self.analisis)):
            return evaluar_riesgo(self.descripcion, 2, 3, ['Identificación'], rol)

    def test_discrepancia_calculada_sin_sobrescribir_usuario(self):
        self.analisis['opinion_llm']['puntaje'] = 1  # No confiar en aritmética del modelo.
        r = self.evaluar()
        self.assertEqual((r['puntaje'], r['nivel']), (6, 'Medio'))
        self.assertEqual((r['valoracion_ia']['puntaje'], r['valoracion_ia']['nivel']), (20, 'Crítico'))
        self.assertEqual(r['valoracion_ia']['diferencia_puntaje'], 14)
        self.assertFalse(r['valoracion_ia']['coincide_con_usuario'])

    def test_referencia_canonica_y_medicion_no_inventada(self):
        r = self.evaluar()
        ref = r['referencias_iso'][0]
        self.assertEqual(ref['codigo'], 'A.3.9')
        self.assertEqual(ref['guia'], 'B.3.9')
        self.assertEqual(ref['norma'], 'ISO/IEC 27701:2025')
        self.assertEqual(ref['fuente'], '/api/fuente-iso/A.3.9')
        self.assertEqual(ref['pagina'], 48)
        self.assertIsNone(r['indicadores_riesgo'][0]['valor_actual'])

    def test_codigo_inventado_y_codigo_2019_descartados_en_toda_api(self):
        for codigo in ['A.7.2.1', 'A.3.999']:
            self.referencia['control'] = codigo
            r = self.evaluar()
            self.assertEqual(r['referencias_iso'], [])
            self.assertEqual(r['analisis_ia']['referencias_iso'], [])
            self.assertTrue(r['avisos_revision'])

    def test_rol_filtra_controles_especificos(self):
        self.referencia['control'] = 'A.1.4.8'
        self.referencia['cita_normativa'] = 'The organization should not retain Pil for longer than is necessary'
        self.assertEqual(self.evaluar('encargado')['referencias_iso'], [])
        self.assertTrue(self.evaluar('responsable')['referencias_iso'])
        self.assertEqual(self.evaluar('no_definido')['referencias_iso'][0]['aplicabilidad'],
                         'Pendiente de confirmar rol')
        mensaje = construir_mensajes({'rol_privacidad': 'encargado', 'contexto_documental': {
            'fragmentos': [{'control': 'A.2.4.3'}]}})[0]['content']
        self.assertNotIn('A.1.4.8', mensaje)
        self.assertIn('A.2.4.3', mensaje)

    def test_evidencia_inventada_o_riesgo_desconectado_se_omiten(self):
        for campo, valor in [('evidencia', 'ya ocurrió una filtración'), ('riesgo', 'Otro riesgo')]:
            with self.subTest(campo=campo):
                original = self.referencia[campo]
                self.referencia[campo] = valor
                self.assertEqual(self.evaluar()['referencias_iso'], [])
                self.referencia[campo] = original
        self.analisis['indicadores_riesgo'][0]['evidencia'] = '1000 cuentas'
        self.assertEqual(self.evaluar()['indicadores_riesgo'], [])

    def test_opinion_sin_datos(self):
        self.analisis['opinion_llm'].update(probabilidad=None, impacto=None)
        validar_analisis(self.analisis)
        r = self.evaluar()['valoracion_ia']
        self.assertIsNone(r['puntaje'])
        self.assertIsNone(r['nivel'])
        self.assertIsNone(r['coincide_con_usuario'])

    def test_opinion_invalida_se_rechaza(self):
        for valor in [True, '4', 4.1, 0, 6, None]:
            self.analisis['opinion_llm']['probabilidad'] = valor
            with self.subTest(valor=valor), self.assertRaises(OllamaError):
                validar_analisis(self.analisis)

    def test_sin_ollama_no_finge_opinion_ni_control(self):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', side_effect=OllamaError('Apagado')):
            r = evaluar_riesgo(self.descripcion, 2, 3)
        self.assertIsNone(r['valoracion_ia'])
        self.assertEqual(r['referencias_iso'], [])
        self.assertEqual(r['indicadores_riesgo'], [])

    def test_api_completa_con_respuesta_http_simulada(self):
        with patch('llm.ollama_client.requests.Session') as session:
            respuesta = session.return_value.__enter__.return_value.request.return_value
            respuesta.status_code = 200
            respuesta.json.return_value = {'message': {'content': json.dumps(self.analisis)}, 'done': True}
            r = app.test_client().post('/api/evaluar', json=dict(descripcion=self.descripcion,
                probabilidad=2, impacto=3, rol_privacidad='responsable'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['valoracion_ia']['puntaje'], 20)
        self.assertEqual(r.json['referencias_iso'][0]['codigo'], 'A.3.9')
        self.assertEqual(len(r.json['indicadores_riesgo']), 1)

    def test_rol_invalido_no_consulta_modelo(self):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama') as llm:
            r = app.test_client().post('/api/evaluar', json=dict(descripcion='Prueba',
                probabilidad=2, impacto=3, rol_privacidad=['responsable']))
            self.assertEqual(r.status_code, 400)
            llm.assert_not_called()
