import os
from pathlib import Path
import unittest
from unittest.mock import patch

from db.repositorio import BaseNoDisponible, conectar, leer_norma, inventario
from knowledge.documento_iso import leer_secciones
from knowledge.documento_ley import leer_articulos
from rag.recuperar_contexto import recuperar_contexto_rag


class TestLecturaPostgres(unittest.TestCase):
    def test_normas_usan_base_sin_leer_archivos(self):
        with patch('db.repositorio.leer_norma', return_value=({'9': {}}, 'huella')) as leer:
            with patch.object(Path, 'read_text', side_effect=AssertionError('Acceso a archivo')):
                leer_secciones()
                leer_articulos()
            self.assertEqual([c.args[0] for c in leer.call_args_list], ['iso','ley'])

    def test_caida_base_no_recurre_a_documentos(self):
        with patch('db.repositorio.leer_fragmentos', side_effect=BaseNoDisponible('fallo')):
            resultado = recuperar_contexto_rag('acceso')
        self.assertEqual(resultado['estado'], 'base_no_disponible')
        self.assertEqual(resultado['fragmentos'], [])

    def test_busqueda_no_llama_embeddings(self):
        fragmento = dict(archivo='politica',pagina=1,fragmento=1,
                        texto='Seguridad acceso confidencialidad permisos personales. ' * 8)
        with patch.dict(os.environ, {'PIMS_BUSQUEDA_SEMANTICA':'0'}), \
                patch('db.repositorio.leer_fragmentos', return_value=[fragmento]), \
                patch('rag.recuperar_contexto.generar_embedding', side_effect=AssertionError('embedding')):
            resultado = recuperar_contexto_rag('Seguridad acceso permisos')
        self.assertEqual(resultado['estado'], 'recuperado')
        self.assertIn('PostgreSQL', resultado['fragmentos'][0]['metodo'])

    def test_busqueda_hibrida_usa_vectores_postgres(self):
        fragmento = dict(archivo='politica',pagina=1,fragmento=1,
                        texto='Seguridad acceso confidencialidad permisos personales. ' * 8)
        with patch.dict(os.environ, {'PIMS_BUSQUEDA_SEMANTICA':'1'}), \
                patch('db.repositorio.leer_fragmentos', return_value=[fragmento]), \
                patch('db.repositorio.leer_vectores', return_value=[(fragmento,[1.,0.])]), \
                patch('rag.recuperar_contexto.generar_embedding', return_value=[1.,0.]):
            resultado = recuperar_contexto_rag('Seguridad acceso permisos')
        self.assertEqual(resultado['fragmentos'][0]['similitud'], 1.)
        self.assertIn('semántica', resultado['mensaje'])

    def test_fallo_embedding_conserva_busqueda_lexica(self):
        fragmento = dict(archivo='politica',pagina=1,fragmento=1,
                        texto='Seguridad acceso confidencialidad permisos personales. ' * 8)
        with patch.dict(os.environ, {'PIMS_BUSQUEDA_SEMANTICA':'1'}), \
                patch('db.repositorio.leer_fragmentos', return_value=[fragmento]), \
                patch('db.repositorio.leer_vectores', return_value=[(fragmento,[1.,0.])]), \
                patch('rag.recuperar_contexto.generar_embedding', side_effect=OSError('fallo')):
            resultado = recuperar_contexto_rag('Seguridad acceso permisos')
        self.assertTrue(resultado['fragmentos'])
        self.assertIn('embeddings no disponibles', resultado['mensaje'])


@unittest.skipUnless(os.getenv('PIMS_TEST_DATABASE') == '1', 'Requiere base exclusiva migrada')
class TestIntegracionPostgres(unittest.TestCase):
    def test_fuentes_y_categorias(self):
        self.assertIn('9', leer_norma('ley')[0])
        self.assertIn('B.3.9', leer_norma('iso')[0])
        self.assertEqual({d['categoria'] for d in inventario()},
                         {'normativa','institucional','proyecto','reporte','evidencia'})
        self.assertTrue(recuperar_contexto_rag('seguridad acceso datos personales')['fragmentos'])

    def test_lector_no_puede_modificar(self):
        with self.assertRaises(BaseNoDisponible) as error:
            with conectar() as con:
                con.execute('DELETE FROM pims_riesgos.documentos WHERE false')
        self.assertEqual(error.exception.__cause__.sqlstate, '42501')

    def test_transaccion_se_revierte(self):
        with self.assertRaises(RuntimeError):
            with conectar(admin=True) as con:
                con.execute("UPDATE pims_riesgos.documentos SET titulo='PRUEBA ROLLBACK' WHERE clave='Ley-29733.md'")
                raise RuntimeError('rollback')
        with conectar() as con:
            titulo = con.execute("SELECT titulo FROM pims_riesgos.documentos WHERE clave='Ley-29733.md'").fetchone()[0]
        self.assertNotEqual(titulo, 'PRUEBA ROLLBACK')

    def test_integridad_originales_y_fuentes_sin_archivos(self):
        import hashlib
        from app import app
        with conectar() as con:
            for original, huella in con.execute('SELECT original,sha256 FROM pims_riesgos.documentos'):
                self.assertEqual(hashlib.sha256(original).hexdigest(), huella)
        with patch.object(Path, 'read_text', side_effect=AssertionError('Fuente en disco')):
            cliente = app.test_client()
            self.assertEqual(cliente.get('/api/fuente-iso/A.3.9').status_code, 200)
            self.assertEqual(cliente.get('/api/fuente-ley/9').status_code, 200)
            self.assertTrue(recuperar_contexto_rag('seguridad acceso')['fragmentos'])

    def test_reimportacion_no_duplica_ni_pierde_vectores(self):
        from db.migrar import migrar
        antes = inventario()
        with conectar() as con:
            vectores = con.execute('SELECT count(*) FROM pims_riesgos.fragmentos WHERE embedding IS NOT NULL').fetchone()[0]
        migrar()
        self.assertEqual(inventario(), antes)
        with conectar() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM pims_riesgos.fragmentos WHERE embedding IS NOT NULL').fetchone()[0], vectores)
