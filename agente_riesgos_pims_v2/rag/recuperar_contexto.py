"""Recuperación híbrida: semántica y términos, con contexto y diversidad de fuentes."""
from collections import Counter
import json
import math
import os
from pathlib import Path
import re
import unicodedata

from requests import RequestException
from rag.embeddings import generar_embedding
from rag.faiss_store import cargar_indice, buscar
from rag.indexar import INDICE, VERSION_INDICE

VACIAS = set("una uno unos unas los las del para por con sin que como esta este estos estas sus sobre entre desde hasta mediante tiene son fue hay ser se de la el en y o a al un es su no lo mas universidad estudiantes datos".split())
TEMAS = [
    (("acceso", "permis", "autentic", "cuenta", "public", "comparte", "compartid"),
     "seguridad confidencialidad acceso autorizado divulgación datos personales"),
    (("conserv", "indefinid", "elimina", "retencion"),
     "conservación finalidad proporcionalidad supresión datos personales"),
    (("consent", "autoriza", "finalidad"),
     "consentimiento finalidad información titular datos personales"),
    (("copia", "respaldo", "perdida"),
     "disponibilidad respaldo recuperación seguridad información"),
]


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def terminos(texto):
    return [t[:7] for t in re.findall(r"[a-z]+", normalizar(texto)) if len(t) > 2 and t not in VACIAS]


def ampliar_consulta(consulta):
    texto = normalizar(consulta)
    temas = [expansion for claves, expansion in TEMAS if any(c in texto for c in claves)]
    return consulta + "\nAspectos de privacidad a contrastar: " + "; ".join(temas) if temas else consulta


def puntajes_lexicos(consulta, fragmentos):
    """BM25 pequeño, calculado sobre el corpus local; no es una confianza."""
    documentos = [Counter(terminos(f["texto"])) for f in fragmentos]
    n = len(documentos)
    media = sum(sum(d.values()) for d in documentos) / max(n, 1) or 1
    palabras = set(terminos(consulta))
    frecuencias = {t: sum(t in d for d in documentos) for t in palabras}
    salida = []
    for documento in documentos:
        longitud = sum(documento.values())
        valor = 0
        for t in palabras:
            tf = documento[t]
            if tf:
                idf = math.log(1 + (n - frecuencias[t] + .5) / (frecuencias[t] + .5))
                valor += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * longitud / media))
        salida.append(valor)
    return salida


def seleccionar(consulta, fragmentos, semanticos, k):
    lexicos = puntajes_lexicos(consulta, fragmentos)
    def clave(f):
        return (f["archivo"], f["pagina"], f["fragmento"])
    indices = {clave(f): i for i, f in enumerate(fragmentos)}
    rangos_sem, similitudes = {}, {}
    for rango, f in enumerate(semanticos, 1):
        i = indices[clave(f)]
        rangos_sem[i] = rango
        similitudes[i] = f["similitud"]
    orden_lex = sorted(range(len(fragmentos)), key=lambda i: lexicos[i], reverse=True)
    rangos_lex = {i: rango for rango, i in enumerate(orden_lex[:30], 1) if lexicos[i] > 0}
    candidatos = set(rangos_sem) | set(rangos_lex)
    puntos = {i: (1 / (20 + rangos_sem[i]) if i in rangos_sem else 0)
                  + (1 / (20 + rangos_lex[i]) if i in rangos_lex else 0)
              for i in candidatos}
    orden = sorted(candidatos, key=lambda i: (-puntos[i], i))
    elegidos, archivos = [], Counter()
    for i in orden:
        f = fragmentos[i]
        if len(f["texto"]) < 180 or archivos[f["archivo"]] >= 2:
            continue
        # No completar la cuota con títulos o resultados sin señal suficiente.
        if lexicos[i] < 1 and similitudes.get(i, 0) < .45:
            continue
        palabras = set(terminos(f["texto"]))
        if any(len(palabras & prev) / max(1, len(palabras | prev)) > .8 for _, prev in elegidos):
            continue
        elegidos.append((i, palabras))
        archivos[f["archivo"]] += 1
        if len(elegidos) == k:
            break
    return [dict(fragmentos[i], id=f"F{n}", similitud=similitudes.get(i),
                 metodo="semántica + términos", relevancia=round(puntos[i], 4))
            for n, (i, _) in enumerate(elegidos, 1)]


def recuperar_contexto_rag(consulta, k=12, carpeta=INDICE):
    try:
        configuracion = json.loads((Path(carpeta) / "configuracion.json").read_text(encoding="utf-8"))
        if (configuracion.get("version") != VERSION_INDICE
                or configuracion.get("modelo") != os.getenv("RAG_EMBED_MODEL", "embeddinggemma")):
            raise ValueError("Índice incompatible")
    except (OSError, ValueError, AttributeError):
        return dict(estado="indice_desactualizado", fragmentos=[],
                    mensaje="Genera el índice compatible: python -m rag.indexar.")
    try:
        idx, fragmentos = cargar_indice(carpeta)
    except (OSError, ValueError, RuntimeError):
        return dict(estado="sin_indice", fragmentos=[], mensaje="Ejecuta python -m rag.indexar después de añadir documentos.")
    try:
        consulta_ampliada = ampliar_consulta(consulta)
        semanticos = buscar(idx, fragmentos, generar_embedding(consulta_ampliada), 30)
        datos = seleccionar(consulta_ampliada, fragmentos, semanticos, k)
    except (RequestException, OSError, ValueError, RuntimeError):
        return dict(estado="error", fragmentos=[], mensaje="No fue posible recuperar el contexto documental.")
    return dict(estado="recuperado" if datos else "sin_coincidencias", fragmentos=datos,
                mensaje="Selección por similitud y términos; verificar fuente, vigencia y aplicabilidad.")
