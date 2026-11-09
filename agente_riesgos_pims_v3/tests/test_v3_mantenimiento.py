"""Regresiones de la consolidación: mantenimiento y corpus sin otra aplicación."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
from db.admin import conectar_admin

class TestMantenimientoV3(TestCase):
    def test_mantenimiento_rechaza_base_ajena(self):
        con = MagicMock()
        con.info.dbname = 'otra_base'
        with patch('db.admin.load_dotenv'), patch.dict('os.environ', {'PIMS_DATABASE_ADMIN_URL': 'dbname=otra_base'}), patch('psycopg.connect') as abrir:
            abrir.return_value.__enter__.return_value = con
            with self.assertRaises(ValueError):
                with conectar_admin(): pass
        con.execute.assert_not_called()

    def test_mantenimiento_exige_configuracion_explicita(self):
        with patch('db.admin.load_dotenv'), patch.dict('os.environ', {}, clear=True), patch('psycopg.connect') as abrir:
            with self.assertRaises(ValueError):
                with conectar_admin(): pass
        abrir.assert_not_called()

    def test_ui_no_ofrece_otra_version(self):
        from app import app
        html = app.test_client().get('/').get_data(as_text=True)
        self.assertNotIn('Abrir PIMS v2', html)
        self.assertNotIn('127.0.0.1:8080', html)
        self.assertIn('Agente PIMS v3', html)
