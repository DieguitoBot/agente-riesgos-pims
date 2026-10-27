"""Indexa los documentos autorizados: python -m rag.indexar."""
import os
import json
from pathlib import Path
from rag.documentos import leer_documentos
from rag.embeddings import generar_embeddings
from rag.faiss_store import crear_indice, guardar_indice

BASE = Path(__file__).resolve().parents[1]
DOCUMENTOS = BASE / "knowledge" / "documentos"
INDICE = BASE / "rag" / "indice_local"
VERSION_INDICE = 2


def indexar(carpeta=DOCUMENTOS, destino=INDICE):
    fragmentos = leer_documentos(carpeta)
    if not fragmentos:
        raise ValueError("No hay textos indexables en knowledge/documentos.")
    lote = max(1, int(os.getenv("RAG_BATCH", "12")))
    vectores = []
    for i in range(0, len(fragmentos), lote):
        vectores.extend(generar_embeddings([f["texto"] for f in fragmentos[i:i + lote]]))
        print(f"Indexando: {min(i + lote, len(fragmentos))}/{len(fragmentos)}", flush=True)
    guardar_indice(crear_indice(vectores), fragmentos, destino)
    (Path(destino) / "configuracion.json").write_text(json.dumps({
        "version": VERSION_INDICE, "modelo": os.getenv("RAG_EMBED_MODEL", "embeddinggemma")
    }), encoding="utf-8")
    return len(fragmentos)


if __name__ == "__main__":
    print("Fragmentos indexados:", indexar())
