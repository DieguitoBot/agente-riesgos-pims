import unittest
from unittest.mock import patch
from llm.ollama_client import OllamaError
from skills.evaluacion_riesgo import evaluar_riesgo

class TestEvaluacionRiesgo(unittest.TestCase):

    def setUp(self):
        parche = patch("skills.evaluacion_riesgo.analizar_con_ollama", side_effect=OllamaError("Ollama no disponible."))
        self.llm = parche.start()
        self.addCleanup(parche.stop)


    def test_riesgo_alto(self):
        resultado = evaluar_riesgo(
            descripcion="La aplicación usa credenciales compartidas y no tiene control de acceso.",
            probabilidad=4,
            impacto=4,
            categorias=["Identificación", "Académicos"]
        )
        self.assertEqual(resultado["nivel"], "Alto")
        self.assertEqual(resultado["puntaje"], 16)

    def test_riesgo_bajo(self):
        resultado = evaluar_riesgo(
            descripcion="Proceso interno controlado.",
            probabilidad=1,
            impacto=2,
            categorias=[]
        )
        self.assertEqual(resultado["nivel"], "Bajo")
        self.assertEqual(resultado["puntaje"], 2)

    def test_matriz_completa(self):
        for p in range(1, 6):
            for i in range(1, 6):
                with self.subTest(p=p, i=i):
                    r = evaluar_riesgo("Prueba", p, i)
                    puntaje = p * i
                    nivel = "Crítico" if puntaje >= 20 else "Alto" if puntaje >= 12 else "Medio" if puntaje >= 6 else "Bajo"
                    self.assertEqual(r["puntaje"], puntaje)
                    self.assertEqual(r["nivel"], nivel)

    def test_fallback_estructurado(self):
        r = evaluar_riesgo("Datos sin autenticacion y sin respaldo", 4, 4, ["Salud"])
        self.assertFalse(r["llm_disponible"])
        self.assertEqual(r["modo"], "reglas_locales")
        self.assertIn("análisis local básico", r["mensaje"])
        self.assertIn("Acceso no autorizado", r["riesgos_identificados"])
        self.assertIn("Pérdida de información", r["riesgos_identificados"])
        self.assertIn("Salud", r["justificacion"])
        self.assertTrue(r["analisis_ia"]["consecuencias"])

    def test_llm_no_modifica_calculo(self):
        self.llm.side_effect = None
        self.llm.return_value = {
            "riesgos_identificados": [{"riesgo": "Uso indebido", "explicacion": "Riesgo inferido."}],
            "consecuencias": ["Posible perjuicio."], "justificacion": "Contexto del nivel Alto.",
            "recomendaciones": ["Revisar permisos."], "puntaje": 1, "nivel": "Bajo",
        }
        r = evaluar_riesgo("Escenario", 4, 4, ["Salud"])
        self.assertTrue(r["llm_disponible"])
        self.assertEqual((r["puntaje"], r["nivel"]), (16, "Alto"))
        self.assertEqual(r["riesgos_identificados"], ["Uso indebido"])
        contexto = self.llm.call_args.args[0]
        self.assertEqual(contexto["categorias"], ["Salud"])
        self.assertEqual(contexto["puntaje"], 16)

    def test_entradas_invalidas_no_consultan_modelo(self):
        casos = [(None, 4, 4, []), (" ", 4, 4, []), (123, 4, 4, []),
                 ("Prueba", True, 4, []), ("Prueba", 4.5, 4, []),
                 ("Prueba", 4, 0, []), ("Prueba", 6, 4, []),
                 ("Prueba", "4", 4, []), ("Prueba", 4, 4, "Salud"),
                 ("Prueba", 4, 4, [1]), ("Prueba", 4, 4, [" "])]
        for args in casos:
            with self.subTest(args=args), self.assertRaises(ValueError):
                evaluar_riesgo(*args)
        self.llm.assert_not_called()

if __name__ == "__main__":
    unittest.main()
