"""Regresiones de sincronización entre plantilla y archivos de interfaz."""
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jinja2 import FileSystemLoader
from app import app


class TestInterfaz(unittest.TestCase):
    def test_elementos_requeridos_por_javascript_existen(self):
        html = app.test_client().get("/").get_data(as_text=True)
        ids = re.findall(r'id="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))
        js = (Path(app.static_folder) / "js/app.js").read_text()
        requeridos = set(re.findall(r'getElementById\("([^"]+)"\)', js))
        self.assertFalse(requeridos - set(ids), requeridos - set(ids))

    def test_actualiza_plantilla_sin_reiniciar_servidor(self):
        with TemporaryDirectory() as carpeta:
            plantilla = Path(carpeta) / "index.html"
            plantilla.write_text('<p id="anterior">Anterior</p>')
            with patch.object(app.jinja_env, "loader", FileSystemLoader(carpeta)):
                app.jinja_env.cache.clear()
                try:
                    cliente = app.test_client()
                    self.assertIn("anterior", cliente.get("/").get_data(as_text=True))
                    fecha = plantilla.stat().st_mtime
                    plantilla.write_text('<p id="estado-rag">Actual</p>')
                    os.utime(plantilla, (fecha + 2, fecha + 2))
                    self.assertIn('id="estado-rag"', cliente.get("/").get_data(as_text=True))
                finally:
                    app.jinja_env.cache.clear()

    def test_html_no_se_guarda_y_versiona_archivos(self):
        respuesta = app.test_client().get("/")
        self.assertTrue(respuesta.cache_control.no_store)
        html = respuesta.get_data(as_text=True)
        for archivo in ("css/style.css", "js/app.js"):
            self.assertRegex(html, re.escape("/static/" + archivo) + r'\?v=[a-f0-9]+')

    def test_version_cambia_al_editar_archivo(self):
        with TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            (base / "js").mkdir()
            (base / "css").mkdir()
            script = base / "js/app.js"
            script.write_text("version anterior")
            (base / "css/style.css").write_text("body {}")
            with patch.object(app, "_static_folder", carpeta):
                cliente = app.test_client()
                anterior = cliente.get("/").get_data(as_text=True)
                script.write_text("version actual")
                actual = cliente.get("/").get_data(as_text=True)
                patron = r'/static/js/app.js[^"]*'
                self.assertNotEqual(re.search(patron, anterior)[0], re.search(patron, actual)[0])
