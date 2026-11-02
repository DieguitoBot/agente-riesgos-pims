import copy
import unittest
from unittest.mock import patch

from skills.revision_contenido import revisar_contenido
from skills.evaluacion_riesgo import evaluar_riesgo
from tests.test_ollama_client import ANALISIS


class TestRevisionContenido(unittest.TestCase):
    def test_carencia_inferida_de_informacion_desconocida_se_advierte(self):
        analisis = copy.deepcopy(ANALISIS)
        analisis['riesgos_identificados'][0].update(
            riesgo='Ausencia de pruebas de restauración',
            explicacion='No se ha confirmado ninguna prueba de restauración.',
            vulnerabilidad='Ausencia de pruebas documentadas.')
        self.assertTrue(any('control desconocido' in a for a in revisar_contenido(analisis)))
        analisis['riesgos_identificados'][0]['explicacion'] = 'El escenario declara que no se realizan pruebas de restauración.'
        self.assertFalse(any('control desconocido' in a for a in revisar_contenido(analisis)))
        analisis['riesgos_identificados'][0].update(
            riesgo='Exposición pública', vulnerabilidad='Ausencia de autenticación.',
            explicacion='El enlace permite lectura sin sesión; no se ha confirmado una filtración activa.')
        self.assertFalse(any('control desconocido' in a for a in revisar_contenido(analisis)))

    def test_indicador_ajeno_y_aplicacion_generica_se_advierten(self):
        analisis = copy.deepcopy(ANALISIS)
        analisis['indicadores_riesgo'] = [dict(
            riesgo='Acceso no autorizado', indicador='Acceso público', evidencia='Conservación indefinida.')]
        analisis['referencias_rag'] = [dict(riesgo=r, aplicacion='La universidad maneja datos.')
                                     for r in ['Acceso no autorizado', 'Conservación indefinida']]
        avisos = revisar_contenido(analisis)
        self.assertTrue(any('hecho diferente' in a for a in avisos))
        self.assertTrue(any('pertinencia RAG' in a for a in avisos))

    def test_alertas_llegan_al_resultado_y_al_inicio_del_reporte(self):
        analisis = copy.deepcopy(ANALISIS)
        analisis['riesgos_identificados'][0].update(
            explicacion='No se menciona un registro (F1).', vulnerabilidad='Ausencia de registro.')
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=analisis), \
                patch('rag.recuperar_contexto.recuperar_contexto_rag', return_value={
                    'estado': 'sin_indice', 'fragmentos': [], 'mensaje': 'Prueba'}):
            r = evaluar_riesgo('Datos sin control de acceso', 3, 4)
        self.assertEqual(r['estado_revision'], 'requiere_revision_por_alertas')
        self.assertTrue(r['reporte_ia_generado'])
        self.assertIn('Borrador con alertas', r['mensaje'])
        encabezado = r['reporte_texto'].split('ESCENARIO')[0]
        self.assertIn('BORRADOR DE IA', encabezado)
        self.assertIn('control desconocido', encabezado)


if __name__ == '__main__':
    unittest.main()
