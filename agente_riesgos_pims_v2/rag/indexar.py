"""Genera embeddings en PostgreSQL: python -m rag.indexar. No escribe índices en disco."""
import os
import math
from pathlib import Path
from psycopg.types.json import Jsonb
from db.repositorio import conectar
from rag.embeddings import generar_embeddings

# Compatibilidad para herramientas que inspeccionan el índice histórico.
BASE = Path(__file__).resolve().parents[1]
INDICE = BASE / 'rag/indice_local'
VERSION_INDICE = 2


def indexar():
    modelo = os.getenv('RAG_EMBED_MODEL', 'embeddinggemma')
    with conectar(admin=True) as con:
        filas = con.execute("""SELECT id,datos FROM pims_riesgos.fragmentos WHERE tipo='rag'
            AND (embedding IS NULL OR modelo_embedding IS DISTINCT FROM %s) ORDER BY id""", (modelo,)).fetchall()
    lote = max(1, int(os.getenv('RAG_BATCH', '12')))
    total = 0
    for inicio in range(0,len(filas),lote):
        grupo = filas[inicio:inicio+lote]
        vectores = generar_embeddings([datos['texto'] for _,datos in grupo])
        if len(vectores) != len(grupo):
            raise ValueError('Embeddings incompletos.')
        with conectar(admin=True) as con:
            for (identificador,datos),vector in zip(grupo,vectores):
                if not vector or any(not math.isfinite(v) for v in vector):
                    raise ValueError('Embedding inválido.')
                total += con.execute("""UPDATE pims_riesgos.fragmentos SET embedding=%s,modelo_embedding=%s
                    WHERE id=%s AND datos=%s""", (vector,modelo,identificador,Jsonb(datos))).rowcount
        print(f'Embeddings guardados en PostgreSQL: {total}/{len(filas)}', flush=True)
    return total


if __name__ == '__main__':
    print('Fragmentos indexados:', indexar())
