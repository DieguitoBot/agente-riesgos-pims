import unittest
from unittest.mock import patch

from app import app
from knowledge.documento_iso import leer_secciones, recuperar_contexto
from prompts.riesgo_prompt import construir_mensajes
from tests import test_complementos


class TestDocumentoISO(unittest.TestCase):
    def test_ocr_secciones_y_trazabilidad(self):
        secciones, huella = leer_secciones()
        self.assertEqual(len(huella), 64)
        acceso = secciones['B.3.9']
        self.assertEqual(acceso['pagina'], 48)
        self.assertIn('individual user access IDs', acceso['texto'])
        self.assertNotIn('B.3.10', acceso['texto'])
        self.assertIn('B.1.2.3', secciones)  # Encabezado sin # y con punto final.
        self.assertIn('B.2.4.3', secciones)  # Encabezado OCR con guion bajo.

    def test_recupera_escenario_universidad_y_envia_texto_real(self):
        documento = recuperar_contexto('cuenta compartida sin permisos y sin respaldo; conservación indefinida', 'responsable')
        codigos = {f['control'] for f in documento['fragmentos']}
        self.assertTrue({'A.3.9', 'A.3.24', 'A.1.4.8'} <= codigos)
        mensajes = construir_mensajes({'contexto_documental': documento})
        self.assertIn('individual user access IDs', mensajes[1]['content'])
        self.assertLessEqual(len(documento['fragmentos']), 8)

    def test_documento_ausente_o_ilegible_no_inventa_contexto(self):
        for error in (FileNotFoundError(), UnicodeError(), StopIteration()):
            with patch('knowledge.documento_iso.leer_secciones', side_effect=error):
                d = recuperar_contexto('sin acceso', 'responsable')
                self.assertEqual(d['estado'], 'no_disponible')
                self.assertEqual(d['fragmentos'], [])

    def test_sin_coincidencias_y_filtrado_por_rol(self):
        self.assertEqual(recuperar_contexto('Descripción insuficiente', 'responsable')['fragmentos'], [])
        d = recuperar_contexto('conservación indefinida', 'encargado')
        self.assertNotIn('A.1.4.8', {f['control'] for f in d['fragmentos']})

    def test_cita_inventada_descartada_aunque_codigo_exista(self):
        caso = test_complementos.TestComplementos()
        caso.setUp()
        caso.referencia['cita_normativa'] = 'ISO requires exactly 90 days of retention.'
        r = caso.evaluar()
        self.assertEqual(r['referencias_iso'], [])
        self.assertEqual(r['analisis_ia']['referencias_iso'], [])
        self.assertTrue(any('cita verificable' in a for a in r['avisos_revision']))

    def test_endpoint_fuente_es_texto_y_codigo_desconocido_404(self):
        cliente = app.test_client()
        r = cliente.get('/api/fuente-iso/A.3.9')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'text/plain')
        self.assertIn('B.3.9 Access rights', r.get_data(as_text=True))
        self.assertEqual(cliente.get('/api/fuente-iso/A.999').status_code, 404)
