"""Regresiones del corpus real y contrato; SQL real se habilita expresamente."""
from pathlib import Path
import os
import unittest
from contextlib import contextmanager
from copy import deepcopy
from unittest.mock import patch

from knowledge.documento_pims import leer_docx
from knowledge.evidencia_rag import validar_citas_rag
from rag.documentos import leer_documentos
from rag.recuperar_contexto import seleccionar, terminos, filtrar_alcance_pims
from skills.evaluacion_riesgo import _nivel_riesgo, evaluar_riesgo
from llm.ollama_client import OllamaError

BASE = Path(__file__).resolve().parents[1]
CARPETA = BASE / 'knowledge/documentos/pims_unsa'


class TestCorpusPIMS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [leer_docx(p) for p in sorted(CARPETA.glob('*.docx'))]
        cls.fs = leer_documentos(CARPETA)

    def test_diez_documentos_con_metadatos_reales(self):
        self.assertEqual(len(self.docs), 10)
        self.assertEqual({d['metadatos']['codigo_documental'] for d in self.docs},
                         {f'PIMS-RIE-{c}' for c in ('01','02','03','03A','04','05A','05B','06','07','21')})
        for doc in self.docs:
            meta = doc['metadatos']
            for campo in ('titulo','version','fecha','responsable','aprobacion','referencias_normativas_declaradas'):
                self.assertTrue(meta[campo], (meta['codigo_documental'], campo))
            self.assertTrue(meta['simulado'])
            self.assertEqual(len(meta['sha256']), 64)
            self.assertIn('pendiente', meta['validacion_normativa'])

    def test_tablas_conservan_cabeceras_filas_y_localizadores(self):
        filas = [f for f in self.fs if 'RIE-002 | TRA-002 | ACT-002' in f['texto']]
        self.assertTrue(filas)
        fila = filas[0]
        self.assertIn('P×I', fila['texto'])
        self.assertIn('A.3.5; A.3.9', fila['texto'])
        self.assertIn('/fila/', fila['localizador'])
        self.assertIsNone(fila['pagina'])
        self.assertFalse(any(f['archivo'].endswith('.txt') for f in self.fs))

    def test_claves_estables_tras_agregar_otra_fuente(self):
        por_doc = {}
        for f in self.fs:
            por_doc.setdefault(f['archivo'], []).append(f['fragmento'])
        for numeros in por_doc.values():
            self.assertEqual(numeros, list(range(1, len(numeros)+1)))

    def test_metodologia_corregida_y_residual_diez_medio(self):
        textos = {d['metadatos']['codigo_documental']: d['contenido'] for d in self.docs}
        self.assertIn('1–5 Bajo; 6–11 Medio; 12–19 Alto; 20–25 Crítico', textos['PIMS-RIE-01'])
        self.assertIn('10 medio', textos['PIMS-RIE-03A'])
        self.assertEqual(_nivel_riesgo(2*5), 'Medio')
        self.assertIn('PENDIENTES DE ANÁLISIS', textos['PIMS-RIE-04'])
        self.assertNotIn('futura matriz D13', textos['PIMS-RIE-04'])

    def test_identificadores_y_criterios_se_recuperan(self):
        self.assertIn('tra-002', terminos('TRA-002'))
        self.assertNotEqual(terminos('PIMS-RIE-03A'), terminos('PIMS-RIE-03'))
        fs = seleccionar('permisos de matrícula TRA-001', self.fs, [], 12, incluir_metodologia=True)
        self.assertEqual(fs[0]['codigo_documental'], 'PIMS-RIE-01')
        self.assertIn('1–5 Bajo', fs[0]['texto'])
        self.assertLessEqual(len(fs), 12)

    def test_no_mezcla_filas_de_otro_tratamiento_explicito(self):
        filtrados = filtrar_alcance_pims('Caso ficticio TRA-001', self.fs)
        self.assertFalse(any('RIE-002 | TRA-002 | ACT-002' in f['texto'] for f in filtrados))
        self.assertTrue(any('RIE-001 | TRA-001 | ACT-001' in f['texto'] for f in filtrados))
        self.assertTrue(any('ACC-001 | RIE-001' in f['texto'] for f in filtrados))
        self.assertFalse(any('ACC-003 | RIE-002' in f['texto'] for f in filtrados))
        self.assertEqual(filtrar_alcance_pims('Consulta sin identificadores', self.fs),self.fs)

    def test_cita_lleva_version_huella_y_localizador(self):
        fuente = dict(self.fs[0], id='F1')
        evidencia = 'Acceso a expedientes de prueba'
        analisis = dict(riesgos_identificados=[{'riesgo':'Acceso'}], referencias_rag=[
            dict(riesgo='Acceso', fuente_id='F1', cita=fuente['texto'][:90],
                 evidencia=evidencia, aplicacion='Propuesta sujeta a revisión')])
        refs, _ = validar_citas_rag(analisis, dict(descripcion=evidencia, contexto_rag={'fragmentos':[fuente]}))
        self.assertEqual(refs[0]['sha256'], fuente['sha256'])
        self.assertEqual(refs[0]['version'], fuente['version'])
        self.assertEqual(refs[0]['localizador'], fuente['localizador'])
        analisis['referencias_rag'][0]['cita'] = 'Cita inventada que no está en la fuente documental.'
        refs, avisos = validar_citas_rag(analisis, dict(descripcion=evidencia, contexto_rag={'fragmentos':[fuente]}))
        self.assertFalse(refs)
        self.assertTrue(avisos)

    def test_reporte_y_calculo_sin_ia_conservan_limites(self):
        fs = [dict(f, id=f'F{n}', similitud=None) for n, f in enumerate(self.fs[:2], 1)]
        with patch('rag.recuperar_contexto.recuperar_contexto_rag', return_value=dict(estado='recuperado',mensaje='prueba',fragmentos=fs)), \
             patch('skills.evaluacion_riesgo.analizar_con_ollama', side_effect=OllamaError('No disponible')):
            r = evaluar_riesgo('Caso ficticio sin control de acceso.', 4, 5)
        self.assertEqual((r['puntaje'],r['nivel']), (20,'Crítico'))
        self.assertIn('simulación académica', r['reporte_texto'])
        self.assertIn(fs[0]['sha256'], r['reporte_texto'])
        self.assertFalse(r['referencias_rag'])

    def test_ia_no_rebaja_prioridad_de_escenario_alto(self):
        analisis = dict(riesgos_identificados=[dict(riesgo='Acceso de prueba',explicacion='Propuesta',prioridad='baja')],
                        consecuencias=['Exposición potencial'],justificacion='Hipótesis',recomendaciones=['Revisar permisos'])
        with patch('skills.evaluacion_riesgo.analizar_con_ollama', return_value=analisis), \
             patch('rag.recuperar_contexto.recuperar_contexto_rag', return_value=dict(estado='sin_coincidencias',mensaje='prueba',fragmentos=[])):
            r = evaluar_riesgo('Caso ficticio de acceso.',3,4)
        self.assertEqual(r['analisis_ia']['riesgos_identificados'][0]['prioridad'],'alta')
        self.assertEqual(r['analisis_ia']['riesgos_identificados'][0]['prioridad_ia'],'baja')
        self.assertEqual((r['puntaje'],r['nivel']), (12,'Alto'))


@unittest.skipUnless(os.getenv('PIMS_TEST_DOCUMENTAL') == '1', 'Requiere corpus PostgreSQL importado e indexado')
class TestPIMSPostgresReal(unittest.TestCase):
    def test_migracion_idempotente_conserva_vectores_y_versiones(self):
        from db.admin import conectar_admin
        from db.migrar import migrar
        from db.repositorio import leer_fuente_rag
        datos = dict(archivo='pims_unsa/prueba.docx', pagina=None, fragmento=1, texto='Texto sintético de prueba',
                     codigo_documental='PIMS-RIE-99', sha256='a'*64)
        doc = ('prueba-documental', 'proyecto', 'Prueba sintética', 'a'*64, datos['texto'], b'original',
               dict(codigo_documental='PIMS-RIE-99',version='prueba'), [('rag','1',datos)])
        with conectar_admin() as con:
            con.execute('SELECT 1')  # Transacción exterior, siempre revertida al finalizar.
            @contextmanager
            def transaccion():
                with con.transaction():
                    yield con
            try:
                with patch('db.migrar.conectar_admin', transaccion), patch('db.migrar.preparar', return_value=[doc]):
                    migrar()
                    con.execute("UPDATE pims_riesgos.fragmentos SET embedding=ARRAY[1.0,0.0],modelo_embedding='prueba' WHERE datos->>'codigo_documental'='PIMS-RIE-99'")
                    migrar()
                    self.assertEqual(con.execute("SELECT count(*) FROM pims_riesgos.documentos WHERE metadatos->>'codigo_documental'='PIMS-RIE-99'").fetchone()[0],1)
                    self.assertIsNotNone(con.execute("SELECT embedding FROM pims_riesgos.fragmentos WHERE datos->>'codigo_documental'='PIMS-RIE-99'").fetchone()[0])
                    nuevo = list(deepcopy(doc))
                    nuevo[0], nuevo[3], nuevo[5] = 'fuente-renombrada', 'b'*64, b'nueva version'
                    nuevo[7][0][2].update(sha256='b'*64,texto='Texto actualizado de prueba')
                    with patch('db.migrar.preparar', return_value=[nuevo]):
                        migrar()
                    self.assertIsNone(con.execute("SELECT embedding FROM pims_riesgos.fragmentos WHERE datos->>'codigo_documental'='PIMS-RIE-99'").fetchone()[0])
                    with patch('db.repositorio.conectar', transaccion):
                        self.assertEqual(leer_fuente_rag('a'*64,'1')['texto'], datos['texto'])
                        self.assertEqual(leer_fuente_rag('b'*64,'1')['texto'], 'Texto actualizado de prueba')
                    self.assertEqual(con.execute("SELECT count(*) FROM pims_riesgos.documentos WHERE metadatos->>'codigo_documental'='PIMS-RIE-99'").fetchone()[0],1)
            finally:
                con.rollback()

    def test_diez_documentos_con_vectores_y_huella_cotejable(self):
        from db.repositorio import inventario, leer_fragmentos, leer_fuente_rag
        docs = [d for d in inventario() if d['metadatos'].get('codigo_documental')]
        self.assertEqual(len(docs),10)
        for doc in docs:
            self.assertGreater(doc['fragmentos'],0)
            self.assertEqual(doc['indexados'], doc['fragmentos'])
        for fuente in leer_fragmentos():
            if fuente.get('codigo_documental'):
                self.assertEqual(leer_fuente_rag(fuente['sha256'], str(fuente['fragmento'])), fuente)


if __name__ == '__main__':
    unittest.main()
