"""Alertas conservadoras de coherencia; no sustituyen una revisión semántica."""
import re
import unicodedata
from collections import defaultdict


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                           if unicodedata.category(c) != 'Mn').split())


def revisar_contenido(analisis):
    avisos = []
    riesgos = {r['riesgo']: r for r in analisis.get('riesgos_identificados', [])}
    for nombre, riesgo in riesgos.items():
        explicacion = normalizar(riesgo.get('explicacion', ''))
        carencia = normalizar(nombre + ' ' + riesgo.get('vulnerabilidad', ''))
        if (re.search(r'ausencia|falta|sin ', carencia)
                and re.search(r'no se menciona|no se ha confirmado (?:ninguna? )?(?:prueba|existencia|realizacion|disponibilidad)|falta de informacion|no se dispone de informacion', explicacion)):
            avisos.append(f'Revisar sustento de «{nombre}»: la explicación menciona información no confirmada. '
                          'No confundir un control desconocido con un control ausente; trasladar lo desconocido a datos por confirmar.')
        if re.search(r'\bF\d+\b', riesgo.get('explicacion', '')):
            avisos.append(f'Revisar atribución de «{nombre}»: los IDs F identifican documentos, no hechos del escenario.')
    for indicador in analisis.get('indicadores_riesgo', []):
        riesgo = riesgos.get(indicador['riesgo'])
        if riesgo and normalizar(indicador['evidencia']) != normalizar(riesgo.get('evidencia', '')):
            avisos.append(f'Revisar indicador «{indicador["indicador"]}»: usa un hecho diferente al del riesgo vinculado. '
                          'Comprobar que fórmula, fuente y umbral miden ese riesgo.')
    aplicaciones = defaultdict(set)
    for ref in analisis.get('referencias_rag', []):
        aplicaciones[normalizar(ref['aplicacion'])].add(ref['riesgo'])
    if any(len(nombres) > 1 for nombres in aplicaciones.values()):
        avisos.append('Revisar pertinencia RAG: se repite la misma aplicación para riesgos distintos. '
                      'Una cita literal no demuestra que sustente cada medida.')
    return avisos
