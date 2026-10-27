"""Valida procedencia literal; la relación semántica sigue requiriendo revisión."""


def normalizar(texto):
    return " ".join(texto.split())


def validar_citas_rag(analisis, contexto):
    fuentes = {f['id']: f for f in contexto.get('contexto_rag', {}).get('fragmentos', [])}
    riesgos = {r['riesgo'] for r in analisis['riesgos_identificados']}
    referencias, avisos = [], []
    for item in analisis.get('referencias_rag', []):
        f = fuentes.get(item.get('fuente_id'))
        cita = normalizar(item.get('cita', ''))
        evidencia = normalizar(item.get('evidencia', ''))
        if (not f or not 20 <= len(cita) <= 240 or cita not in normalizar(f['texto'])
                or item.get('riesgo') not in riesgos or len(evidencia) < 8
                or evidencia.casefold() not in normalizar(contexto['descripcion']).casefold()
                or not item.get('aplicacion', '').strip()):
            avisos.append('Se omitió una relación RAG sin cita literal, fuente recuperada o hecho del escenario.')
            continue
        referencias.append(dict(item, cita=cita, archivo=f['archivo'], pagina=f['pagina'],
                                fragmento=f['fragmento'],
                                estado='Cita cotejada con el fragmento; aplicabilidad por revisar'))
    if fuentes and not referencias:
        avisos.append('Se recuperaron documentos, pero el modelo no aportó relaciones RAG con citas verificables.')
    return referencias, list(dict.fromkeys(avisos))
