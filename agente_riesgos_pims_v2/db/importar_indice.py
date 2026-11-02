"""Migra una vez los vectores históricos; solo acepta fragmentos idénticos en PostgreSQL."""
import json
import os
from pathlib import Path
from psycopg.types.json import Jsonb
from db.repositorio import conectar


def importar():
    from rag.faiss_store import cargar_indice
    carpeta = Path(__file__).resolve().parents[1] / 'rag/indice_local'
    configuracion = json.loads((carpeta / 'configuracion.json').read_text())
    if configuracion.get('version') != 2 or configuracion.get('modelo') != os.getenv('RAG_EMBED_MODEL','embeddinggemma'):
        raise ValueError('Índice histórico incompatible; ejecutar python -m rag.indexar para regenerar en PostgreSQL.')
    indice, fragmentos = cargar_indice(carpeta)
    total = 0
    with conectar(admin=True) as con:
        for i, fragmento in enumerate(fragmentos):
            vector = indice.reconstruct(i).tolist()
            total += con.execute("""UPDATE pims_riesgos.fragmentos SET embedding=%s,modelo_embedding=%s
                WHERE tipo='rag' AND datos=%s""", (vector, configuracion['modelo'], Jsonb(fragmento))).rowcount
    return total


if __name__ == '__main__':
    print('Vectores migrados y cotejados:', importar())
