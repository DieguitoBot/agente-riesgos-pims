"""Recuperación semántica sin ejecutar instrucciones incluidas en los documentos."""
from requests import RequestException
from rag.embeddings import generar_embedding
from rag.faiss_store import cargar_indice, buscar
from rag.indexar import INDICE


def recuperar_contexto_rag(consulta, k=4, carpeta=INDICE):
    try:
        idx, fragmentos = cargar_indice(carpeta)
    except (OSError, ValueError, RuntimeError):
        return dict(estado="sin_indice", fragmentos=[], mensaje="Ejecuta python -m rag.indexar después de añadir documentos.")
    try:
        datos = buscar(idx, fragmentos, generar_embedding(consulta), k)
    except (RequestException, OSError, ValueError, RuntimeError):
        return dict(estado="error", fragmentos=[], mensaje="No fue posible generar el embedding de consulta.")
    return dict(estado="recuperado" if datos else "sin_coincidencias", fragmentos=datos,
                mensaje="Fragmentos por similitud; verificar fuente, vigencia y aplicabilidad.")
