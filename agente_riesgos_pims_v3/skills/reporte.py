"""Reporte exportable del análisis validado; no necesita otra llamada al modelo."""
from mantenimiento.metricas import medir
from datetime import datetime, timezone


def generar_anexo_tecnico(r):
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
    if r.get('metodologia'):
        partes.extend(['Método: ' + r['metodologia']['formula'], 'Bandas: ' + r['metodologia']['bandas'],
                       'Aceptación: ' + r['metodologia']['aceptacion']])
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
        if riesgo.get('prioridad_ia') and riesgo['prioridad_ia'] != riesgo.get('prioridad'):
            partes.append('Prioridad sugerida por IA: ' + riesgo['prioridad_ia']
                          + '; prevalece revisión alta por la matriz académica.')
    partes.append('\nCONTROLES ISO ESPECÍFICOS')
    if not r['referencias_iso']:
        partes.append('Sin relaciones normativas verificables. Esto no acredita cumplimiento.')
    for ref in r['referencias_iso']:
        if ref.get('decision_soa'):
            partes.extend([f"SoA {ref.get('version_soa')}: {ref['decision_soa']}",
                'Justificación SoA: '+ref.get('justificacion_soa','Por revisar'),
                'Implementación: '+ref.get('estado_implementacion','No acreditada'),
                'Acciones documentadas: '+ref.get('acciones_documentadas','Por programar')])
        if ref.get('estado_ocr'):
            partes.append('OCR: '+ref['estado_ocr']+' · '+(ref.get('correccion_ocr') or 'Sin corrección de identificador registrada'))
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
        if ref.get('codigo_documental'):
            partes.append(f"{ref['codigo_documental']} · versión {ref['version']} · {ref['localizador']} · SHA256 {ref['sha256']}")
        partes.extend([f"{ref['fuente_id']} · {ref['archivo']} · página {ref['pagina'] or 'no aplica'} · fragmento {ref['fragmento']}",
                       'Riesgo: ' + ref['riesgo'], 'Hecho: ' + ref['evidencia'],
                       'Cita: ' + ref['cita'], 'Aplicación propuesta: ' + ref['aplicacion'],
                       'Verificación: ' + ref['estado']])
    partes.append('\nFUENTES RECUPERADAS PARA CONSULTA')
    for fuente in r.get('fuentes_rag', []):
        if fuente.get('codigo_documental'):
            partes.append(f"{fuente['codigo_documental']} · versión {fuente['version']} · {fuente['localizador']} · SHA256 {fuente['sha256']} · relevancia {fuente.get('relevancia')} · similitud {fuente.get('similitud')}")
        partes.append(f"{fuente['id']} · {fuente['archivo']} · página {fuente['pagina'] or 'no aplica'} · fragmento {fuente['fragmento']}")
        if fuente.get('tipo_fuente') != 'iso':
            partes.append('Extracto recuperado: ' + fuente['texto'])
        else:
            partes.append('Normativa privada: consultar localizador; se exportan solo citas seleccionadas.')
    partes.append('\nINDICADORES PROPUESTOS')
    for item in r['indicadores_riesgo']:
        partes.extend([item['indicador'] + ' · ' + item['riesgo'], 'Hecho: ' + item['evidencia'],
                       'Fórmula: ' + item['formula'], 'Fuente: ' + item['fuente_datos'],
                       'Frecuencia: ' + item['frecuencia'], 'Umbral propuesto: ' + item['umbral_propuesto'],
                       'Valor actual: pendiente de medición'])
    partes.extend(['\nCONSECUENCIAS', *r['consecuencias'], '\nRECOMENDACIONES', *r['recomendaciones'],
                   '\nTRAZABILIDAD Y LÍMITES', 'Matriz académica: probabilidad × impacto; no impuesta por ISO.',
                   'Evaluación inicial de riesgos; no certifica incumplimientos, realiza auditorías ni decide sanciones.',
                   'La selección temática no es exhaustiva. Las citas acreditan procedencia textual, no interpretación ni implementación.',
                   *r['avisos_revision']])
    for clave in ('documentacion_iso', 'documentacion_ley'):
        doc = r[clave]
        partes.extend([clave + ': ' + doc['estado'], 'SHA256: ' + (doc['sha256'] or 'No disponible'), doc['mensaje']])
    return '\n'.join(partes) + '\n'


def preparar_reporte(r):
    """Estructura propia alineada a RIE-06; no completa datos mediante inferencias."""
    import re
    descripcion=r.get('descripcion','')
    def ids(prefijo):
        return ', '.join(sorted(set(re.findall(r'\b'+prefijo+r'-\d{3}\b',descripcion)))) or 'No identificado; confirmar con inventario'
    revision={'requiere_revision_por_alertas':'Requiere revisión por alertas','pendiente_de_revision':'Pendiente de revisión humana','sin_analisis_ia':'Sin análisis de IA'}.get(r.get('estado_revision'),'Pendiente de revisión humana')
    soa=r.get('documentacion_soa',{})
    referencias=[]
    for campo in ('referencias_iso','referencias_ley','referencias_rag'):
        for ref in r.get(campo,[]):
            categoria=('implementación PIMS' if ref.get('codigo_documental') else
                       'institucional' if ref.get('categoria')=='institucional' else
                       'normativa' if campo!='referencias_rag' or ref.get('categoria')=='normativa' else 'otra fuente')
            referencias.append(dict(ref,categoria_reporte=categoria))
    secciones=[
        ('1. Resumen ejecutivo',[
            f"Valoración inicial del escenario: {r['puntaje']}/25 — {r['nivel']}. Probabilidad e impacto declarados por el usuario; cálculo Python.",
            f"Se identificaron {len(r.get('riesgos_identificados',[]))} riesgos propuestos. Estado de revisión: {revision}.",
            f"Relaciones documentales cotejadas: {len(referencias)}. La aceptación residual y la aprobación institucional están pendientes."]),
        ('2. Objetivo y alcance',[
            'Evaluar el escenario declarado, orientar tratamiento y dejar evidencia documental para revisión académica.',
            'Alcance de esta evaluación: '+descripcion,
            'Alcance documental PIMS: tres tratamientos hipotéticos de matrícula, bienestar y biblioteca. No se extrapolan hechos a toda la UNSA.']),
        ('3. Tratamiento, datos y activos',[
            'Tratamiento declarado: '+ids('TRA')+'; rol: '+r.get('rol_privacidad','no_definido')+'.',
            'Activos declarados: '+ids('ACT')+'; riesgos documentales declarados: '+ids('RIE')+'.',
            'Categorías de datos declaradas: '+(', '.join(r.get('categorias',[])) or 'No informadas')+'.',
            'Propietario, volumen, sistemas, base jurídica y destinatarios: confirmar; no asignados automáticamente.']),
        ('4. Metodología y cálculo determinista',[
            f"Probabilidad: {r['probabilidad']}/5; impacto: {r['impacto']}/5; P × I = {r['puntaje']}/25; nivel {r['nivel']}.",
            'Bandas académicas: 1–5 Bajo; 6–11 Medio; 12–19 Alto; 20–25 Crítico. PIMS-RIE-01 revisión 0.2.',
            'Altos/Críticos: plan y prioridad alta. La matriz no sustituye decisiones humanas ni obligaciones legales.',
            'El LLM no altera P/I, puntaje o nivel principal. La opinión IA se presenta por separado; no es medición.']),
        ('5. Riesgos y consecuencias',[
            'Interpretación del LLM, sujeta a revisión: '+r.get('justificacion','No informada.'),
            'Consecuencias propuestas para personas y contexto: '+('; '.join(r.get('consecuencias',[])) or 'Por determinar')+'.',
            'Consecuencias organizativas: sin valoración diferenciada acreditada; no se estiman sanciones ni daños económicos.']),
        ('6. Controles y aplicabilidad',[
            'Solo se relacionan controles con evidencia literal y justificación contextual del análisis; recuperar un nombre no acredita aplicabilidad.',
            f"SoA consultada: {soa.get('version') or 'No disponible'}; controles revisados en documento: {soa.get('total_revisados',0)}; SHA256 {soa.get('sha256') or 'no disponible'}.",
            'Estados de implementación: propuestas o pendientes; no se aportó evidencia operativa institucional.']),
        ('7. Tratamiento, responsables y riesgo residual',[
            'Las medidas detalladas son propuestas, sin autorización institucional. Responsables y plazos: por acordar salvo registro humano explícito en el plan vigente.',
            'Riesgo residual estimado: no asignado automáticamente. Las proyecciones de PIMS-RIE-03A son supuestos documentales, no resultados operativos.',
            'Riesgo residual confirmado: no disponible sin verificación; aceptación residual: pendiente de decisión del propietario.',
            'Las actividades, evidencias de cierre y modificaciones humanas se conservan por separado del reporte original.']),
        ('8. Evidencias y referencias documentales',[
            'Las referencias se distinguen entre normativa, institucional e implementación PIMS. Cotejo literal no equivale a validez de la inferencia.',
            'Identificadores, versiones, páginas/líneas OCR y huellas acompañan las fuentes consultadas. La fuente ISO privada no se reproduce íntegramente.']),
        ('9. Conclusiones',[
            f"El escenario obtiene {r['puntaje']}/25 ({r['nivel']}) según las entradas declaradas; requiere revisión humana de hechos, controles y tratamiento.",
            'La documentación sustenta propuestas cuando existe una relación cotejada. No acredita implantación real, aprobación o conformidad de la UNSA.']),
        ('10. Recomendaciones',r.get('recomendaciones',[]) or ['Completar la evidencia y revisar el escenario.']),
        ('11. Limitaciones y aprobación',[
            'SIMULACIÓN ACADÉMICA. No se utilizan datos personales auténticos ni se inventan propietarios, plazos o evidencias.',
            'ISO/IEC 27701:2025 procede de OCR autorizado; las tablas A y numeración deterioradas requieren cotejo con el PDF.',
            'La SoA tiene cobertura sistemática de revisión, con decisiones abiertas; no es una declaración institucional aprobada.',
            'Elaboración automática: Agente PIMS V3. Revisión humana: pendiente. Aprobación: no otorgada.',
            *r.get('avisos_revision',[])]),
    ]
    return dict(codigo='PIMS-RIE-06',version=r.get('version_reporte','PIMS-RIE-06 / legado'),
        identificador=r.get('evaluacion_id',r.get('experimento_id','No informado')),
        fecha=r.get('fecha_evaluacion','No informada en el registro original'),
        estado='BORRADOR CON ALERTAS' if r.get('alertas_contenido') else 'BORRADOR PARA REVISIÓN HUMANA',
        origen='Ollama local + cálculo Python + PostgreSQL' if r.get('llm_disponible') else 'Reglas locales — REPORTE IA NO DISPONIBLE',
        secciones=[dict(titulo=t,parrafos=p) for t,p in secciones],referencias=referencias,
        riesgos=r.get('analisis_ia',{}).get('riesgos_identificados',[]))


@medir('reporte.txt')
def generar_reporte(r):
    datos=preparar_reporte(r)
    partes=['UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA',
        'IMPLEMENTACIÓN ACADÉMICA SIMULADA · PIMS',
        'INFORME DE EVALUACIÓN Y TRATAMIENTO DE RIESGOS DE PRIVACIDAD',
        f"{datos['version']} · Evaluación {datos['identificador']}",
        'Fecha UTC: '+datos['fecha'],'Estado: '+datos['estado'],'Origen: '+datos['origen']]
    for seccion in datos['secciones']:
        partes.extend(['\n'+seccion['titulo'],*seccion['parrafos']])
    partes.extend(['\nANEXO TÉCNICO — ANÁLISIS, CONTROLES Y TRAZABILIDAD',generar_anexo_tecnico(r)])
    return '\n'.join(partes)+'\n'
