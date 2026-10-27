import json
import unittest
from unittest.mock import patch

import requests

from config import obtener_configuracion
from llm.ollama_client import (OllamaError, analizar_con_ollama, consultar_estado,
                               recuperar_analisis)

ANALISIS = {
    "riesgos_identificados": [{"riesgo": "Acceso no autorizado", "explicacion": "No se declaran controles.",
        "evidencia": "sin control de acceso", "amenaza": "Consulta por terceros",
        "vulnerabilidad": "Permisos no delimitados", "dano_personas": "Divulgación de datos",
        "medida_concreta": "Definir roles de acceso", "verificacion": "Comprobar rechazo de cuenta sin rol",
        "prioridad": "alta"}],
    "consecuencias": ["Posible divulgación."],
    "justificacion": "El puntaje proporcionado es 16 y el nivel Alto.",
    "recomendaciones": ["Aplicar roles."],
    "opinion_llm": {"probabilidad": 5, "impacto": 4,
                    "justificacion_probabilidad": "Exposición elevada.",
                    "justificacion_impacto": "Posible daño a personas.",
                    "confianza": "media", "datos_faltantes": ["Volumen de registros"]},
    "indicadores_riesgo": [], "referencias_iso": [], "referencias_ley": [],
}


class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        env = patch.dict("os.environ", {"OLLAMA_URL": "http://127.0.0.1:11434",
                                       "OLLAMA_MODEL": "qwen3.5:4b-q4_K_M", "OLLAMA_TIMEOUT": "120"})
        env.start()
        self.addCleanup(env.stop)
        parche = patch("llm.ollama_client.requests.Session")
        self.session = parche.start().return_value.__enter__.return_value
        self.addCleanup(parche.stop)
        self.response = self.session.request.return_value
        self.response.status_code = 200
        self.response.json.return_value = {"message": {"content": json.dumps(ANALISIS)}, "done": True}

    def test_presupuestos_invalidos_se_rechazan(self):
        for entorno in ({'OLLAMA_NUM_CTX': '0'}, {'OLLAMA_NUM_PREDICT': '-1'},
                        {'OLLAMA_NUM_CTX': 'texto'},
                        {'OLLAMA_NUM_CTX': '4096', 'OLLAMA_NUM_PREDICT': '4096'}):
            with self.subTest(entorno=entorno), patch.dict('os.environ', entorno):
                with self.assertRaises(ValueError):
                    obtener_configuracion()

    def test_chat_json_y_contexto(self):
        resultado = analizar_con_ollama({"descripcion": "Datos sin control de acceso", "puntaje": 16, "nivel": "Alto", "categorias": ["Salud"]})
        self.assertEqual(resultado, ANALISIS)
        args, kwargs = self.session.request.call_args
        self.assertEqual(args, ("POST", "http://127.0.0.1:11434/api/chat"))
        self.assertFalse(kwargs["json"]["stream"])
        self.assertEqual(kwargs["json"]["format"]["type"], "object")
        self.assertIn("Salud", kwargs["json"]["messages"][1]["content"])
        self.assertFalse(self.session.trust_env)

    def test_json_cercado_y_texto_adicional(self):
        for texto in [json.dumps(ANALISIS), '```json\n' + json.dumps(ANALISIS) + '\n```',
                      'Respuesta:\n' + json.dumps(ANALISIS) + '\nFin.']:
            with self.subTest(texto=texto):
                self.assertEqual(recuperar_analisis(texto), ANALISIS)

    def test_json_invalido_y_tipos(self):
        casos = [None, 'No es JSON', '{"incompleto":', '[]', '{}',
                 json.dumps(dict(ANALISIS, riesgos_identificados=["riesgo"])),
                 json.dumps(dict(ANALISIS, consecuencias="texto")),
                 json.dumps(dict(ANALISIS, recomendaciones=[1])),
                 json.dumps(dict(ANALISIS, justificacion=" "))]
        for texto in casos:
            with self.subTest(texto=texto), self.assertRaises(OllamaError):
                recuperar_analisis(texto)

    def test_descarta_campos_matematicos_del_modelo(self):
        r = recuperar_analisis(json.dumps(dict(ANALISIS, puntaje=1, nivel="Bajo")))
        self.assertEqual(r, ANALISIS)

    def test_errores_http_y_red(self):
        for error in [requests.ConnectionError(), requests.Timeout(), requests.RequestException()]:
            with self.subTest(error=error), self.assertRaises(OllamaError):
                self.session.request.side_effect = error
                analizar_con_ollama({})
        self.session.request.side_effect = None
        for codigo in [404, 500, 302]:
            self.response.status_code = codigo
            with self.subTest(codigo=codigo), self.assertRaises(OllamaError) as cm:
                analizar_con_ollama({})
            if codigo == 404:
                self.assertIn("ollama pull qwen3.5:4b-q4_K_M", str(cm.exception))

    def test_respuesta_http_invalida(self):
        self.response.json.side_effect = ValueError("JSON inválido")
        with self.assertRaises(OllamaError):
            analizar_con_ollama({})
        self.response.json.side_effect = None
        for respuesta in [[], {}, {"message": None}, {"message": {"content": "{}"}}, {"done": False}]:
            self.response.json.return_value = respuesta
            with self.subTest(respuesta=respuesta), self.assertRaises(OllamaError):
                analizar_con_ollama({})

    def test_status_modelo_instalado_y_ausente(self):
        self.response.json.return_value = {"models": [{"name": "qwen3.5:4b-q4_K_M"}]}
        estado = consultar_estado()
        self.assertTrue(estado["ollama"])
        self.assertEqual(estado["modelos_instalados"], ["qwen3.5:4b-q4_K_M"])
        self.assertEqual(estado["timeout_segundos"], 120)
        self.response.json.return_value = {"models": []}
        estado = consultar_estado()
        self.assertFalse(estado["ollama"])
        self.assertTrue(estado["servicio_disponible"])
        self.assertIn("ollama pull", estado["mensaje"])

    def test_respuesta_truncada_informa_limite(self):
        self.response.json.return_value = {
            "done": True, "done_reason": "length", "message": {"content": "{}"}}
        with self.assertRaisesRegex(OllamaError, "límite de generación"):
            analizar_con_ollama({})

    def test_status_sin_servicio(self):
        self.session.request.side_effect = requests.ConnectionError()
        self.assertFalse(consultar_estado()["ollama"])

    def test_configuracion_invalida_activa_error_controlado(self):
        for variable, valor in [("OLLAMA_TIMEOUT", "nan"), ("OLLAMA_TIMEOUT", "0"),
                                ("OLLAMA_TIMEOUT", "abc"), ("OLLAMA_URL", "https://ollama.com"),
                                ("OLLAMA_MODEL", "modelo:cloud")]:
            with self.subTest(variable=variable), patch.dict("os.environ", {variable: valor}):
                with self.assertRaises(OllamaError):
                    analizar_con_ollama({})
                self.assertFalse(consultar_estado()["ollama"])
        self.session.request.assert_not_called()

    def test_modelo_configurable(self):
        with patch.dict("os.environ", {"OLLAMA_MODEL": "otro:3b"}):
            self.assertEqual(obtener_configuracion()["modelo"], "otro:3b")
            analizar_con_ollama({"descripcion": "Datos sin control de acceso"})
            self.assertEqual(self.session.request.call_args.kwargs["json"]["model"], "otro:3b")
