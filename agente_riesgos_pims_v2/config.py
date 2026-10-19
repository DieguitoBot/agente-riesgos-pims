"""Configuración local; se lee del entorno sin necesitar un archivo .env."""
import math
import os
from urllib.parse import urlsplit


def obtener_modelo():
    return os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()


def obtener_configuracion(modelo_solicitado=None):
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    modelo = obtener_modelo() if modelo_solicitado is None else modelo_solicitado
    if not isinstance(modelo, str) or len(modelo) > 160:
        raise ValueError("Modelo inválido.")
    modelo = modelo.strip()
    try:
        timeout = float(os.getenv("OLLAMA_TIMEOUT", "300"))
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
    return {"url": url, "modelo": modelo, "timeout": timeout}
