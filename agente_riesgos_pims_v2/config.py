"""Configuración local; se lee del entorno sin necesitar un archivo .env."""
import math
import os
from urllib.parse import urlsplit


def obtener_modelo():
    return os.getenv("OLLAMA_MODEL", "qwen3.5:4b-q4_K_M").strip()


def obtener_configuracion(modelo_solicitado=None):
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    modelo = obtener_modelo() if modelo_solicitado is None else modelo_solicitado
    if not isinstance(modelo, str) or len(modelo) > 160:
        raise ValueError("Modelo inválido.")
    modelo = modelo.strip()
    try:
        timeout = float(os.getenv("OLLAMA_TIMEOUT", "900"))
    except ValueError as exc:
        raise ValueError("OLLAMA_TIMEOUT debe ser un número positivo de segundos.") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("OLLAMA_TIMEOUT debe ser un número positivo de segundos.")
    partes = urlsplit(url)
    if (partes.scheme != "http" or partes.hostname not in {"localhost", "127.0.0.1", "::1"}
            or partes.username or partes.password or partes.path or partes.query or partes.fragment):
        raise ValueError("OLLAMA_URL debe apuntar a Ollama local, por ejemplo http://127.0.0.1:11434.")
    if not modelo or modelo.endswith(":cloud"):
        raise ValueError("OLLAMA_MODEL debe indicar un modelo local instalado, sin sufijo :cloud.")
    limites = {}
    for variable, defecto in (("OLLAMA_NUM_CTX", 32768), ("OLLAMA_NUM_PREDICT", 16384)):
        try:
            valor = int(os.getenv(variable, str(defecto)))
        except ValueError as exc:
            raise ValueError(f"{variable} debe ser un entero positivo.") from exc
        if valor <= 0:
            raise ValueError(f"{variable} debe ser un entero positivo.")
        limites[variable] = valor
    if limites["OLLAMA_NUM_PREDICT"] >= limites["OLLAMA_NUM_CTX"]:
        raise ValueError("OLLAMA_NUM_CTX debe superar OLLAMA_NUM_PREDICT para reservar espacio a las fuentes.")
    return {"url": url, "modelo": modelo, "timeout": timeout,
            "num_ctx": limites["OLLAMA_NUM_CTX"], "num_predict": limites["OLLAMA_NUM_PREDICT"]}
