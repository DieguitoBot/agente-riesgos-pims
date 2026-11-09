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
