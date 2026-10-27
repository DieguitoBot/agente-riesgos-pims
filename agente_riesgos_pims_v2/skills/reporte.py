"""Reporte exportable del análisis validado; no necesita otra llamada al modelo."""
from datetime import datetime, timezone


def generar_reporte(r):
    ia = r['llm_disponible']
    partes = ['REPORTE DE EVALUACIÓN DE RIESGOS DE PRIVACIDAD',
              'Origen: análisis de IA con validación de estructura y procedencia de citas' if ia else 'Origen: reglas locales. REPORTE IA NO DISPONIBLE.',
              'Fecha UTC: ' + datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'Modelo: ' + r['modelo'], 'Estado: ' + r['mensaje'],
              '\nESCENARIO', r['descripcion'], 'Rol: ' + r['rol_privacidad'],
              'Datos: ' + (', '.join(r['categorias']) or 'No declarados'),
              '\nVALORACIÓN DEL USUARIO',
              f"Probabilidad {r['probabilidad']}/5 · Impacto {r['impacto']}/5 · {r['puntaje']}/25 · {r['nivel']}"]
    if ia:
        revision = ['BORRADOR DE IA — requiere revisión de contenido. Las citas cotejadas no validan las inferencias.']
        revision.extend(r.get('alertas_contenido', []))
        partes[1:1] = revision
    opinion = r['valoracion_ia']
    partes.append('\nVALORACIÓN DE LA IA')
    if opinion:
        partes.extend([f"Probabilidad {opinion['probabilidad']} · Impacto {opinion['impacto']} · Puntaje {opinion['puntaje']} · Nivel {opinion['nivel']}",
                       'Probabilidad: ' + opinion['justificacion_probabilidad'],
                       'Impacto: ' + opinion['justificacion_impacto'],
                       'Confianza declarada: ' + opinion['confianza'],
                       'Información faltante: ' + ('; '.join(opinion['datos_faltantes']) or 'No indicada')])
    else:
        partes.append('El informe breve de IA no incluyó una valoración numérica.' if r.get('formato_ia') == 'breve'
                       else 'No se recibió una opinión válida del modelo.')
    partes.extend(['\nANÁLISIS', r['justificacion'], '\nRIESGOS Y TRATAMIENTO'])
    for i, riesgo in enumerate(r['analisis_ia']['riesgos_identificados'], 1):
        partes.append(f"{i}. {riesgo['riesgo']}")
        for campo, titulo in [('explicacion', 'Análisis'), ('evidencia', 'Hecho'), ('vulnerabilidad', 'Vulnerabilidad'),
                             ('amenaza', 'Amenaza'), ('dano_personas', 'Daño potencial'), ('medida_concreta', 'Medida'),
                             ('verificacion', 'Criterio de cierre'), ('prioridad', 'Prioridad')]:
            if riesgo.get(campo):
                partes.append(titulo + ': ' + riesgo[campo])
    partes.append('\nCONTROLES ISO ESPECÍFICOS')
    if not r['referencias_iso']:
        partes.append('Sin relaciones normativas verificables. Esto no acredita cumplimiento.')
    for ref in r['referencias_iso']:
        partes.extend([f"{ref['codigo']} — {ref['nombre']} · Anexo A · Guía {ref['guia']} del anexo B",
                       'Riesgo: ' + ref['riesgo'], 'Hecho: ' + ref['evidencia'],
                       'Relación: ' + ref['motivo'], 'Cita: ' + ref['cita_normativa'],
                       'Estado: ' + ref['estado'], 'Aplicabilidad: ' + ref['aplicabilidad'],
                       'Evidencia pendiente: ' + ref['evidencia_requerida'],
                       f"Fuente: {ref['archivo']} · página OCR {ref['pagina']} · línea {ref['linea']}"])
    partes.append('\nLEY 29733: ARTÍCULOS RELACIONADOS CON EL RIESGO')
    if not r['referencias_ley']:
        partes.append('Sin relaciones legales sustentadas en este análisis.')
    for ref in r['referencias_ley']:
        partes.extend([f"Artículo {ref['articulo']} — {ref['titulo']}",
                       'Riesgo: ' + ref['riesgo'], 'Hecho: ' + ref['evidencia'],
                       'Relación: ' + ref['motivo'], 'Cita: ' + ref['cita_normativa'],
                       'Estado: ' + ref['estado'], 'Evidencia pendiente: ' + ref['evidencia_requerida'],
                       f"Fuente: {ref['archivo']} · línea {ref['linea']}"])
    partes.append('\nSUSTENTO DOCUMENTAL DEL RAG')
    partes.append(r.get('estado_rag', 'Estado no informado'))
    referencias_rag = r.get('referencias_rag', [])
    if not referencias_rag:
        partes.append('Sin relaciones RAG con cita verificable. Recuperar una fuente no acredita que sustente el análisis.')
    for ref in referencias_rag:
        partes.extend([f"{ref['fuente_id']} · {ref['archivo']} · página {ref['pagina'] or 'no aplica'} · fragmento {ref['fragmento']}",
                       'Riesgo: ' + ref['riesgo'], 'Hecho: ' + ref['evidencia'],
                       'Cita: ' + ref['cita'], 'Aplicación propuesta: ' + ref['aplicacion'],
                       'Verificación: ' + ref['estado']])
    partes.append('\nFUENTES RECUPERADAS PARA CONSULTA')
    for fuente in r.get('fuentes_rag', []):
        partes.extend([f"{fuente['id']} · {fuente['archivo']} · página {fuente['pagina'] or 'no aplica'} · fragmento {fuente['fragmento']}",
                       'Extracto recuperado: ' + fuente['texto']])
    partes.append('\nINDICADORES PROPUESTOS')
    for item in r['indicadores_riesgo']:
        partes.extend([item['indicador'] + ' · ' + item['riesgo'], 'Hecho: ' + item['evidencia'],
                       'Fórmula: ' + item['formula'], 'Fuente: ' + item['fuente_datos'],
                       'Frecuencia: ' + item['frecuencia'], 'Umbral propuesto: ' + item['umbral_propuesto'],
                       'Valor actual: pendiente de medición'])
    partes.extend(['\nCONSECUENCIAS', *r['consecuencias'], '\nRECOMENDACIONES', *r['recomendaciones'],
                   '\nTRAZABILIDAD Y LÍMITES', 'Matriz académica: probabilidad × impacto; no impuesta por ISO.',
                   'Evaluación inicial de riesgos; no certifica incumplimientos, realiza auditorías ni decide sanciones.',
                   'Catálogo ISO y recuperación temática parciales. Las citas acreditan procedencia textual, no interpretación.',
                   *r['avisos_revision']])
    for clave in ('documentacion_iso', 'documentacion_ley'):
        doc = r[clave]
        partes.extend([clave + ': ' + doc['estado'], 'SHA256: ' + (doc['sha256'] or 'No disponible'), doc['mensaje']])
    return '\n'.join(partes) + '\n'
