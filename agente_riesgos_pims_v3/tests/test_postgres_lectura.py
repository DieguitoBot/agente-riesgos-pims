"""Pruebas SQL sin modificar el corpus: PIMS_TEST_LECTURA=1 python -m unittest
tests.test_postgres_lectura -v.
"""
import os
import unittest

from db.repositorio import (
    conectar, DATOS_FRAGMENTO_SQL, leer_fragmentos, leer_norma, leer_vectores,
)


@unittest.skipUnless(os.getenv('PIMS_TEST_LECTURA') == '1', 'Requiere PostgreSQL local')
class TestLecturaEsquemas(unittest.TestCase):
    def test_columnas_prevalecen_sobre_json_historico(self):
        with conectar() as con:
            datos = con.execute(f"""WITH f AS (
                SELECT '{{"archivo":"politica.md","texto":"Texto anterior","fragmento":1}}'::jsonb AS datos,
                    'Texto vigente'::text AS texto, 12 AS pagina, 24 AS linea,
                    'B.3.9'::text AS seccion, 'Acceso'::text AS titulo,
                    ARRAY[1.0,0.0] AS embedding, 'interno'::text AS busqueda
                ) SELECT {DATOS_FRAGMENTO_SQL} FROM f""").fetchone()[0]
        self.assertEqual(datos['texto'], 'Texto vigente')
        self.assertEqual(datos['archivo'], 'politica.md')
        self.assertEqual((datos['pagina'], datos['linea']), (12, 24))
        self.assertEqual(datos['seccion'], 'B.3.9')
        self.assertNotIn('embedding', datos)
        self.assertNotIn('busqueda', datos)

    def test_esquema_historico_conserva_texto_y_pagina_nula(self):
        with conectar() as con:
            datos = con.execute(f"""WITH f AS (
                SELECT '{{"archivo":"ley.md","texto":"Texto histórico","fragmento":1}}'::jsonb AS datos,
                    5 AS id, 'rag'::text AS tipo
                ) SELECT {DATOS_FRAGMENTO_SQL} FROM f""").fetchone()[0]
        self.assertEqual(datos, dict(archivo='ley.md', texto='Texto histórico', fragmento=1, pagina=None))

    def test_columnas_nulas_no_borran_procedencia_historica(self):
        with conectar() as con:
            datos = con.execute(f"""WITH f AS (
                SELECT '{{"texto":"Texto histórico","pagina":7,"linea":3}}'::jsonb AS datos,
                    NULL::text AS texto, NULL::integer AS pagina, NULL::integer AS linea
                ) SELECT {DATOS_FRAGMENTO_SQL} FROM f""").fetchone()[0]
        self.assertEqual(datos, dict(texto='Texto histórico', pagina=7, linea=3))

    def test_corpus_real_y_vectores_comparten_texto_y_procedencia(self):
        fragmentos = leer_fragmentos()
        self.assertTrue(fragmentos)
        por_clave = {(f['archivo'], f['pagina'], f['fragmento']): f for f in fragmentos}
        for f in fragmentos:
            self.assertTrue(f['texto'].strip())
        for f, vector in leer_vectores(os.getenv('RAG_EMBED_MODEL', 'embeddinggemma')):
            self.assertEqual(f, por_clave[(f['archivo'], f['pagina'], f['fragmento'])])
            self.assertTrue(vector)
        for tipo, codigo in (('iso', 'B.3.9'), ('ley', '9')):
            normas, huella = leer_norma(tipo)
            self.assertTrue(normas[codigo]['texto'].strip())
            self.assertTrue(normas[codigo]['linea'])
            self.assertEqual(len(huella), 64)
