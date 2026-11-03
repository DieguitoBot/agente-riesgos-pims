"""Embeddings locales mediante Ollama. Instalar modelo con ollama pull embeddinggemma."""
import os
import requests


def generar_embeddings(textos, consulta=False):
    if not textos:
        return []
    url = os.getenv("RAG_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    if url not in ("http://127.0.0.1:11434", "http://localhost:11434"):
        raise ValueError("La URL de embeddings debe ser local.")
    modelo = os.getenv("RAG_EMBED_MODEL", "embeddinggemma")
    # Prefijos de recuperación documentados por Google para EmbeddingGemma.
    if modelo.split(":")[0] == "embeddinggemma":
        prefijo = "task: search result | query: " if consulta else "title: none | text: "
        textos = [prefijo + texto for texto in textos]
    r = requests.post(url + "/api/embed", json={"model": modelo, "input": textos}, timeout=180)
    r.raise_for_status()
    vectors = r.json().get("embeddings", [])
    if len(vectors) != len(textos) or any(not v for v in vectors):
        raise ValueError("Embeddings incompletos.")
    return vectors


def generar_embedding(texto):
    return generar_embeddings([texto], consulta=True)[0]
