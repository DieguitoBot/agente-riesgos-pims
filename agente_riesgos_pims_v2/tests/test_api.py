import json
import unittest
from unittest.mock import patch

import requests

from app import app
from tests.test_ollama_client import ANALISIS


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.datos = {"descripcion": "Datos sin control de acceso", "probabilidad": 4,
                      "impacto": 4, "categorias": ["Salud"]}
        parche = patch("llm.ollama_client.requests.Session")
        self.session = parche.start().return_value.__enter__.return_value
        self.addCleanup(parche.stop)
        self.session.request.side_effect = requests.ConnectionError()

    def test_rutas_frontend(self):
        for ruta in ["/", "/static/css/style.css", "/static/js/app.js"]:
            with self.client.get(ruta) as respuesta:
                self.assertEqual(respuesta.status_code, 200)
        html = self.client.get("/").get_data(as_text=True)
        for campo in ['id="consecuencias"', 'id="modo"', 'id="mensaje"']:
            self.assertIn(campo, html)

    def test_evaluacion_fallback(self):
        respuesta = self.client.post("/api/evaluar", json=self.datos)
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertEqual((resultado["puntaje"], resultado["nivel"]), (16, "Alto"))
        self.assertFalse(resultado["llm_disponible"])
        self.assertIn("recomendaciones", resultado["analisis_ia"])

    def test_evaluacion_llm(self):
        self.session.request.side_effect = None
        self.session.request.return_value.status_code = 200
        self.session.request.return_value.json.return_value = {"message": {"content": json.dumps(ANALISIS)}}
        resultado = self.client.post("/api/evaluar", json=self.datos).get_json()
        self.assertTrue(resultado["llm_disponible"])
        self.assertEqual(resultado["analisis_ia"], ANALISIS)
        self.assertEqual(resultado["puntaje"], 16)

    def test_llm_invalido_modelo_ausente_y_timeout_usan_fallback(self):
        self.session.request.side_effect = None
        response = self.session.request.return_value
        for codigo, contenido in [(200, {"message": {"content": "JSON inválido"}}), (404, {}), (500, {})]:
            response.status_code = codigo
            response.json.return_value = contenido
            respuesta = self.client.post("/api/evaluar", json=self.datos)
            self.assertEqual(respuesta.status_code, 200)
            self.assertFalse(respuesta.get_json()["llm_disponible"])
        self.session.request.side_effect = requests.Timeout()
        self.assertFalse(self.client.post("/api/evaluar", json=self.datos).get_json()["llm_disponible"])

    def test_entradas_invalidas(self):
        for datos in [[], "texto", {}, dict(self.datos, descripcion=None),
                      dict(self.datos, probabilidad=True), dict(self.datos, impacto=4.9),
                      dict(self.datos, categorias=[1]), dict(self.datos, categorias="Salud")]:
            with self.subTest(datos=datos):
                r = self.client.post("/api/evaluar", json=datos)
                self.assertEqual(r.status_code, 400)
                self.assertIn("error", r.get_json())
        r = self.client.post("/api/evaluar", data="{mal", content_type="application/json")
        self.assertEqual(r.status_code, 400)
        self.session.request.assert_not_called()

    def test_status_sin_servicio_y_con_modelo(self):
        respuesta = self.client.get("/api/status")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.get_json()["ollama"])
        self.session.request.side_effect = None
        response = self.session.request.return_value
        response.status_code = 200
        response.json.return_value = {"models": [{"name": "qwen2.5:3b"}]}
        with patch.dict("os.environ", {"OLLAMA_MODEL": "qwen2.5:3b"}):
            self.assertTrue(self.client.get("/api/status").get_json()["ollama"])
