import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

try:
    from rag.documentos import dividir, leer_documentos
    from rag.recuperar_contexto import seleccionar, recuperar_contexto_rag
    from rag.embeddings import generar_embeddings, generar_embedding
    DISPONIBLE = True
except ImportError:
    DISPONIBLE = False


@unittest.skipUnless(DISPONIBLE, 'Dependencias RAG opcionales no instaladas')
class TestRAGCalidad(unittest.TestCase):
    def test_segmentos_no_cortan_palabras_ni_crean_colas(self):
        texto = ' '.join(f'palabra{i}' for i in range(330))
        bloques = dividir(texto)
        self.assertGreater(len(bloques), 1)
        self.assertTrue(all(len(b) >= 180 for b in bloques))
        self.assertTrue(all(p.startswith('palabra') for b in bloques for p in b.split()))
        self.assertEqual(set(texto.split()), set(' '.join(bloques).split()))

    def test_omite_portadas_y_conserva_articulos(self):
        with TemporaryDirectory() as carpeta:
            Path(carpeta, 'ley.md').write_text('# Título\n\n## Artículo 9\n' +
                'Seguridad de los datos personales y restricciones de acceso. ' * 8 +
                '\n## Artículo 10\n' + 'Conservación limitada a la finalidad declarada. ' * 8)
            fs = leer_documentos(carpeta)
        self.assertEqual(len(fs), 2)
        self.assertTrue(fs[0]['texto'].startswith('## Artículo 9'))
        self.assertTrue(fs[1]['texto'].startswith('## Artículo 10'))
        self.assertTrue(all(f['archivo'] == 'ley.md' for f in fs))

    def test_prefijos_diferencian_documento_y_consulta(self):
        with patch.dict('os.environ', {'RAG_EMBED_MODEL': 'embeddinggemma'}), patch('rag.embeddings.requests.post') as pedir:
            pedir.return_value.json.return_value = {'embeddings': [[1, 0]]}
            generar_embeddings(['Documento'])
            self.assertEqual(pedir.call_args.kwargs['json']['input'], ['title: none | text: Documento'])
            generar_embedding('Consulta')
            self.assertEqual(pedir.call_args.kwargs['json']['input'], ['task: search result | query: Consulta'])

    def test_filtra_colas_y_diversifica_fuentes(self):
        fs = [
            dict(archivo='estatuto.pdf', pagina=1, fragmento=1, texto='Rectorado.'),
            dict(archivo='ley.md', pagina=None, fragmento=2, texto='Seguridad de datos personales y acceso autorizado. ' * 7),
            dict(archivo='politica.md', pagina=None, fragmento=3, texto='Confidencialidad de registros. Restringir permisos a personal autorizado. ' * 6),
        ]
        semanticos = [dict(f, similitud=.8-i*.1) for i, f in enumerate(fs)]
        seleccion = seleccionar('seguridad acceso confidencialidad permisos', fs, semanticos, 4)
        self.assertEqual({f['archivo'] for f in seleccion}, {'ley.md', 'politica.md'})
        self.assertEqual([f['id'] for f in seleccion], ['F1', 'F2'])

    def test_indice_antiguo_requiere_reindexar_sin_consultar_modelo(self):
        with TemporaryDirectory() as carpeta, patch('rag.recuperar_contexto.generar_embedding') as generar:
            r = recuperar_contexto_rag('acceso', carpeta=carpeta)
            self.assertEqual(r['estado'], 'indice_desactualizado')
            generar.assert_not_called()
