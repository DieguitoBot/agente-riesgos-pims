"""Genera embeddings en PostgreSQL: python -m rag.indexar. No escribe índices en disco."""
import os
import math
from psycopg.types.json import Jsonb
from db.repositorio import DATOS_FRAGMENTO_SQL
from db.admin import conectar_admin
from rag.embeddings import generar_embeddings

def indexar():
    modelo = os.getenv('RAG_EMBED_MODEL', 'embeddinggemma')
    with conectar_admin() as con:
        filas = con.execute(f"""SELECT f.id, {DATOS_FRAGMENTO_SQL}
            FROM pims_riesgos.fragmentos f WHERE f.tipo='rag'
            AND (f.embedding IS NULL OR f.modelo_embedding IS DISTINCT FROM %s)
            ORDER BY f.id""", (modelo,)).fetchall()
    lote = max(1, int(os.getenv('RAG_BATCH', '12')))
    total = 0
    for inicio in range(0,len(filas),lote):
        grupo = filas[inicio:inicio+lote]
        vectores = generar_embeddings([datos['texto'] for _,datos in grupo])
        if len(vectores) != len(grupo):
            raise ValueError('Embeddings incompletos.')
        with conectar_admin() as con:
            for (identificador,datos),vector in zip(grupo,vectores):
                if not vector or any(not math.isfinite(v) for v in vector):
                    raise ValueError('Embedding inválido.')
                total += con.execute(f"""UPDATE pims_riesgos.fragmentos f
                    SET embedding=%s,modelo_embedding=%s
                    WHERE f.id=%s AND ({DATOS_FRAGMENTO_SQL})=%s""",
                    (vector,modelo,identificador,Jsonb(datos))).rowcount
        print(f'Embeddings guardados en PostgreSQL: {total}/{len(filas)}', flush=True)
    return total


if __name__ == '__main__':
    print('Fragmentos indexados:', indexar())
