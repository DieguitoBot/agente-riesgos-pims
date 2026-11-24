"""Contratos de consolidación; normativa de prueba sintética, nunca copia ISO."""
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import hashlib
import os

from knowledge.documento_iso import leer_secciones
from knowledge.documento_pims import leer_docx
from knowledge.revision_soa import CATALOGO, decision
from skills.evaluacion_riesgo import evaluar_riesgo
from skills.reporte import preparar_reporte
from llm.ollama_client import OllamaError

BASE=Path(__file__).resolve().parents[1]

class TestConsolidacion(TestCase):
    def test_ocr_corrige_solo_identificador_conserva_original_y_limites(self):
        with TemporaryDirectory() as tmp:
            ruta=Path(tmp)/'sintetico.md'
            texto=('6.1.3. Privacy risk treatment\nSynthetic treatment requirement.\n6.2 Privacy objectives\nOther.\n'
                '## Annex A\nTable A.1 — Synthetic controllers\nTest one.\nTable A.2 — Synthetic processors\nTest two.\n'
                'Table A.3 — Synthetic shared\nTest three.\n## Annex B\n<!-- Page 36 -->\n'
                '#### B.1.4.3 Limit processing\nControl\nSynthetic first control.\nImplementation guidance\nSynthetic first guidance.\n'
                '#### B.14.4 Accuracy and quality\nControl\nSynthetic accuracy control.\nImplementation guidance\nSynthetic accuracy guidance.\n## Annex C\n')
            ruta.write_text(texto);antes=ruta.read_bytes();secciones,huella=leer_secciones(ruta)
            self.assertEqual(ruta.read_bytes(),antes)
            self.assertEqual(huella,hashlib.sha256(antes).hexdigest())
            self.assertTrue({'6.1.3','A.1','A.2','A.3','B.1.4.4'}<=set(secciones))
            self.assertIn('B.14.4',secciones['B.1.4.4']['texto'])
            self.assertIn('→',secciones['B.1.4.4']['correccion_ocr'])
            self.assertNotIn('accuracy',secciones['B.1.4.3']['texto'])
            self.assertNotIn('6.2',secciones['6.1.3']['texto'])

    def test_soa_revisa_universo_por_rol_sin_implementaciones_inventadas(self):
        doc=leer_docx(BASE/'knowledge/documentos/pims_unsa/PIMS-RIE-04_SoA_Extracto.docx')
        controles=doc['metadatos']['controles_soa']
        self.assertEqual({c['codigo'] for c in controles},set(CATALOGO))
        self.assertEqual(len(controles),78)
        self.assertEqual(Counter(c['codigo'].split('.')[1] for c in controles),{'1':31,'2':18,'3':29})
        self.assertTrue(all(c['aplicabilidad']=='Pendiente de rol' for c in controles if c['codigo'].startswith('A.2.')))
        self.assertEqual(sum(c['aplicabilidad']=='Incluido propuesto' for c in controles),11)
        self.assertFalse(any(c['estado']=='Implementado' for c in controles))
        self.assertTrue(all(c['justificacion'] and c['fuente'] and c['observaciones'] for c in controles))

    def resultado(self):
        with patch('skills.evaluacion_riesgo.analizar_con_ollama',side_effect=OllamaError('Prueba sin IA')):
            return evaluar_riesgo('Caso ficticio TRA-001 ACT-001 RIE-001: permisos excesivos.',3,4,['Identificación'],'responsable')

    def test_reporte_identificable_y_campos_pendientes_explicitos(self):
        r=self.resultado();d=preparar_reporte(r)
        self.assertEqual(d['identificador'],r['evaluacion_id'])
        self.assertIn(r['evaluacion_id'],r['reporte_texto'])
        self.assertIn('IMPLEMENTACIÓN ACADÉMICA SIMULADA',r['reporte_texto'])
        self.assertIn('PIMS-RIE-06 / 1.0',r['reporte_texto'])
        self.assertIn('residual',r['reporte_texto'])
        self.assertIn('por acordar',r['reporte_texto'])
        self.assertIn('SHA256',r['reporte_texto'])
        self.assertIn('REPORTE IA NO DISPONIBLE',r['reporte_texto'])
        self.assertEqual((r['puntaje'],r['nivel']),(12,'Alto'))

    def test_html_escapa_escenario_y_preserva_exportaciones(self):
        from app import app
        r=self.resultado();r['descripcion']='<img src=x onerror=alert(1)>'
        detalle=dict(id=r['evaluacion_id'],creado=r['fecha_evaluacion'],resultado=r,planes=[])
        with patch('app.gestion.obtener_evaluacion',return_value=detalle):
            respuesta=app.test_client().get('/api/experimento/evaluaciones/'+r['evaluacion_id']+'/reporte?formato=html')
        html=respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code,200)
        self.assertNotIn('<img src=x',html)
        self.assertIn('&lt;img src=x',html)
        self.assertIn('Imprimir / guardar PDF',html)
        self.assertIn('Aceptación',r['reporte_texto'])


@skipUnless(os.getenv('PIMS_TEST_CONSOLIDACION')=='1','Requiere fuentes importadas e indexadas en PostgreSQL')
class TestNormativaSQLReal(TestCase):
    def test_iso_core_tablas_y_guias_en_postgres(self):
        from db.repositorio import leer_norma,leer_fragmentos,leer_soa,inventario
        secciones,huella=leer_norma('iso')
        self.assertEqual(len(secciones),86)
        self.assertTrue({'6.1.3','A.1','A.2','A.3','B.1.4.4'}<=set(secciones))
        self.assertTrue(secciones['B.1.4.4']['correccion_ocr'])
        self.assertEqual(len(leer_soa()['controles']),78)
        docs=[d for d in inventario() if d['sha256']==huella]
        self.assertEqual(len(docs),1)
        fs=[f for f in leer_fragmentos() if f.get('tipo_fuente')=='iso']
        self.assertTrue(fs)
        self.assertTrue(all(f['sha256']==huella and f['categoria']=='normativa' for f in fs))
