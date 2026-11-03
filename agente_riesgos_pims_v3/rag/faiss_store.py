"""Índice FAISS: similitud coseno de embeddings normalizados."""
import json
from pathlib import Path
import faiss
import numpy as np


def crear_indice(vectores):
    m = np.asarray(vectores, dtype="float32")
    if m.ndim != 2 or m.shape[0] == 0:
        raise ValueError("Se necesitan vectores uniformes.")
    faiss.normalize_L2(m)
    idx = faiss.IndexFlatIP(m.shape[1])
    idx.add(m)
    return idx


def guardar_indice(idx, fragmentos, carpeta):
    p = Path(carpeta)
    p.mkdir(parents=True, exist_ok=True)
    if idx.ntotal != len(fragmentos):
        raise ValueError("Índice y fragmentos no coinciden.")
    faiss.write_index(idx, str(p / "indice.faiss"))
    (p / "fragmentos.json").write_text(json.dumps(fragmentos, ensure_ascii=False), encoding="utf-8")


def cargar_indice(carpeta):
    p = Path(carpeta)
    idx = faiss.read_index(str(p / "indice.faiss"))
    items = json.loads((p / "fragmentos.json").read_text(encoding="utf-8"))
    if idx.ntotal != len(items):
        raise ValueError("Metadatos incompatibles.")
    return idx, items


def buscar(idx, fragmentos, vector, k=4):
    v = np.asarray([vector], dtype="float32")
    if v.shape[1] != idx.d:
        raise ValueError("Dimensión distinta; vuelve a indexar con el mismo modelo.")
    faiss.normalize_L2(v)
    scores, ids = idx.search(v, min(k, idx.ntotal))
    return [dict(fragmentos[int(i)], similitud=round(float(s), 4)) for s, i in zip(scores[0], ids[0]) if i >= 0]
