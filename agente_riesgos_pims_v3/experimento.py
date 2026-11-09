"""Persistencia de PIMS v3: resultados originales y planes editables separados."""
import csv
from datetime import date, datetime
import io
import uuid

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from db.repositorio import conectar

ESTADOS = ('propuesto', 'en_revision', 'aprobado', 'en_curso', 'verificado', 'descartado')


class NoEncontrado(LookupError):
    pass


class Conflicto(ValueError):
    pass


def serializar(valor):
    if isinstance(valor, (date, datetime, uuid.UUID)):
        return valor.isoformat() if hasattr(valor, 'isoformat') else str(valor)
    if isinstance(valor, dict):
        return {k: serializar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [serializar(v) for v in valor]
    return valor


def identificador(valor):
    try:
        return uuid.UUID(str(valor))
    except (ValueError, TypeError) as exc:
        raise NoEncontrado('Evaluación no encontrada.') from exc


def referencias_riesgo(resultado, riesgo):
    refs = []
    for campo, tipo, codigo in (('referencias_iso','ISO','codigo'),
                                ('referencias_ley','Ley','articulo'),
                                ('referencias_rag','RAG','fuente_id')):
        for ref in resultado.get(campo, []):
            if ref['riesgo'] == riesgo:
                refs.append({'tipo': tipo, 'codigo': ref[codigo], 'archivo': ref.get('archivo', ''),
                             'cita': ref.get('cita_normativa', ref.get('cita', ''))})
    return refs


def guardar_evaluacion(resultado, duracion=0, procedencia='ollama_experimental'):
    if not resultado.get('reporte_ia_generado') and procedencia != 'demostracion':
        raise ValueError('Solo se guardan evaluaciones de IA válidas.')
    evaluacion = uuid.uuid4()
    with conectar() as con:
        con.execute('''INSERT INTO gestitel_experimental.evaluaciones
            (id,titulo,procedencia,duracion_segundos,resultado,reporte_base)
            VALUES (%s,%s,%s,%s,%s,%s)''', (evaluacion, resultado['descripcion'][:120],
            procedencia, duracion, Jsonb(resultado), resultado['reporte_texto']))
        for n, riesgo in enumerate(resultado['analisis_ia']['riesgos_identificados'], 1):
            plan_id = con.execute('''INSERT INTO gestitel_experimental.tratamientos
                (evaluacion_id,codigo,riesgo,hecho,amenaza,vulnerabilidad,dano,medida,
                 verificacion,prioridad,referencias)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (evaluacion, f'R-{n:02}', riesgo['riesgo'], riesgo.get('evidencia', ''),
                 riesgo.get('amenaza', ''), riesgo.get('vulnerabilidad', ''),
                 riesgo.get('dano_personas', ''), riesgo.get('medida_concreta', ''),
                 riesgo.get('verificacion', ''), riesgo.get('prioridad', ''),
                 Jsonb(referencias_riesgo(resultado, riesgo['riesgo'])))).fetchone()[0]
            if riesgo.get('medida_concreta'):
                con.execute('''INSERT INTO gestitel_experimental.actividades
                    (tratamiento_id,orden,descripcion) VALUES (%s,1,%s)''',
                    (plan_id, riesgo['medida_concreta']))
    return str(evaluacion)


def listar_evaluaciones():
    with conectar() as con:
        with con.cursor(row_factory=dict_row) as cur:
            filas = cur.execute('''SELECT e.id,e.creado,e.titulo,e.procedencia,
                e.duracion_segundos,count(t.id) AS riesgos
                FROM gestitel_experimental.evaluaciones e
                LEFT JOIN gestitel_experimental.tratamientos t ON t.evaluacion_id=e.id
                GROUP BY e.id ORDER BY e.creado DESC LIMIT 100''').fetchall()
    return serializar(filas)


def _planes(con, evaluacion):
    with con.cursor(row_factory=dict_row) as cur:
        planes = cur.execute('''SELECT * FROM gestitel_experimental.tratamientos
            WHERE evaluacion_id=%s ORDER BY id''', (evaluacion,)).fetchall()
        for plan in planes:
            plan['actividades'] = cur.execute('''SELECT id,descripcion,responsable,fecha_fin,completada
                FROM gestitel_experimental.actividades WHERE tratamiento_id=%s ORDER BY orden,id''',
                (plan['id'],)).fetchall()
    return serializar(planes)


def obtener_evaluacion(valor):
    evaluacion = identificador(valor)
    with conectar() as con:
        with con.cursor(row_factory=dict_row) as cur:
            fila = cur.execute('SELECT * FROM gestitel_experimental.evaluaciones WHERE id=%s',
                               (evaluacion,)).fetchone()
        if not fila:
            raise NoEncontrado('Evaluación no encontrada.')
        fila['planes'] = _planes(con, evaluacion)
    return serializar(fila)


def texto(datos, campo, limite=5000):
    valor = datos.get(campo, '')
    if not isinstance(valor, str) or len(valor) > limite:
        raise ValueError(f'{campo}: texto inválido o demasiado largo.')
    return valor.strip()


def fecha(datos, campo):
    valor = datos.get(campo)
    if valor in (None, ''):
        return None
    try:
        if not isinstance(valor, str):
            raise ValueError()
        return date.fromisoformat(valor).isoformat()
    except ValueError as exc:
        raise ValueError(f'{campo}: usa una fecha válida AAAA-MM-DD.') from exc


def validar_plan(datos):
    if not isinstance(datos, dict):
        raise ValueError('Envía un objeto JSON con el plan.')
    if type(datos.get('version')) is not int or datos['version'] < 1:
        raise ValueError('La versión del plan debe ser un entero positivo.')
    estado = datos.get('estado')
    if estado not in ESTADOS:
        raise ValueError('Estado de tratamiento inválido.')
    salida = {c: texto(datos, c, 160 if c in ('responsable','area','verificado_por') else 5000)
              for c in ('responsable','area','medida','verificacion','evidencia_verificacion','verificado_por')}
    if not salida['medida'] or not salida['verificacion']:
        raise ValueError('La medida y su verificación son obligatorias.')
    salida.update({c: fecha(datos, c) for c in ('fecha_inicio','fecha_fin','fecha_verificacion')})
    if salida['fecha_inicio'] and salida['fecha_fin'] and salida['fecha_fin'] < salida['fecha_inicio']:
        raise ValueError('La fecha final no puede ser anterior al inicio.')
    if estado in ('aprobado','en_curso','verificado') and not salida['responsable']:
        raise ValueError('Asigna un responsable antes de aprobar o ejecutar el plan.')
    if estado == 'verificado' and not all(salida[c] for c in ('evidencia_verificacion','verificado_por','fecha_verificacion')):
        raise ValueError('Para verificar se requiere evidencia, nombre del verificador y fecha.')
    if salida['fecha_verificacion'] and salida['fecha_verificacion'] > date.today().isoformat():
        raise ValueError('La fecha de verificación no puede ser futura.')
    for campo in ('probabilidad_residual','impacto_residual'):
        valor = datos.get(campo)
        if valor is not None and (type(valor) is not int or not 1 <= valor <= 5):
            raise ValueError('La valoración residual usa enteros de 1 a 5 o valores vacíos.')
        salida[campo] = valor
    p, i = salida['probabilidad_residual'], salida['impacto_residual']
    if (p is None) != (i is None):
        raise ValueError('Completa ambas cifras residuales o deja ambas vacías.')
    if p is not None and estado != 'verificado':
        raise ValueError('Reevalúa el riesgo residual después de verificar la medida.')
    actividades = datos.get('actividades', [])
    if not isinstance(actividades, list) or len(actividades) > 50:
        raise ValueError('El plan admite hasta 50 actividades.')
    salida['actividades'] = []
    for actividad in actividades:
        if not isinstance(actividad, dict):
            raise ValueError('Actividad inválida.')
        a = {c: texto(actividad, c, 3000 if c == 'descripcion' else 160)
             for c in ('descripcion','responsable')}
        if not a['descripcion']:
            raise ValueError('Cada actividad necesita una descripción.')
        a['fecha_fin'] = fecha(actividad, 'fecha_fin')
        a['completada'] = actividad.get('completada', False)
        if type(a['completada']) is not bool:
            raise ValueError('El estado de una actividad debe ser booleano.')
        if a['completada'] and not a['responsable']:
            raise ValueError('Indica quién realizó cada actividad completada.')
        salida['actividades'].append(a)
    if estado == 'verificado' and any(not a['completada'] for a in salida['actividades']):
        raise ValueError('Completa las actividades antes de verificar el plan.')
    salida.update(estado=estado, version=datos['version'])
    return salida


def actualizar_plan(plan_id, datos):
    nuevo = validar_plan(datos)
    with conectar() as con:
        with con.cursor(row_factory=dict_row) as cur:
            previo = cur.execute('SELECT * FROM gestitel_experimental.tratamientos WHERE id=%s FOR UPDATE',
                                  (plan_id,)).fetchone()
            if not previo:
                raise NoEncontrado('Plan no encontrado.')
            if previo['version'] != nuevo['version']:
                raise Conflicto('El plan cambió en otra ventana. Recarga la evaluación antes de guardar.')
            antes = next(p for p in _planes(con, previo['evaluacion_id']) if p['id'] == plan_id)
            campos = ('responsable','area','medida','verificacion','fecha_inicio','fecha_fin','estado',
                      'evidencia_verificacion','verificado_por','fecha_verificacion',
                      'probabilidad_residual','impacto_residual')
            # Los nombres son constantes de código, nunca datos del usuario.
            cur.execute('UPDATE gestitel_experimental.tratamientos SET ' +
                        ','.join(c+'=%s' for c in campos) +
                        ',version=version+1,actualizado=now() WHERE id=%s',
                        tuple(nuevo[c] for c in campos)+(plan_id,))
            cur.execute('DELETE FROM gestitel_experimental.actividades WHERE tratamiento_id=%s', (plan_id,))
            for n, a in enumerate(nuevo['actividades'], 1):
                cur.execute('''INSERT INTO gestitel_experimental.actividades
                    (tratamiento_id,orden,descripcion,responsable,fecha_fin,completada)
                    VALUES (%s,%s,%s,%s,%s,%s)''',
                    (plan_id,n,a['descripcion'],a['responsable'],a['fecha_fin'],a['completada']))
            despues = next(p for p in _planes(con, previo['evaluacion_id']) if p['id'] == plan_id)
            cur.execute('INSERT INTO gestitel_experimental.cambios(tratamiento_id,antes,despues) VALUES (%s,%s,%s)',
                        (plan_id,Jsonb(antes),Jsonb(despues)))
    return despues


def comparar(evaluacion):
    r, planes = evaluacion['resultado'], evaluacion['planes']
    return {
        'riesgos': len(planes), 'referencias_verificadas': {
            c: len(r.get(c, [])) for c in ('referencias_iso','referencias_ley','referencias_rag')},
        'con_responsable': sum(bool(p['responsable']) for p in planes),
        'con_plazo': sum(bool(p['fecha_fin']) for p in planes),
        'verificados': sum(p['estado'] == 'verificado' for p in planes),
        'actividades': sum(len(p['actividades']) for p in planes),
        'alertas_ia': r.get('alertas_contenido', []),
        'nota': 'La comparación conserva el mismo análisis original. Mide organización y seguimiento; no demuestra mayor precisión normativa.'}


def residual(plan):
    p, i = plan['probabilidad_residual'], plan['impacto_residual']
    return f'{p} × {i} = {p*i}/25' if p is not None and i is not None else 'Pendiente de reevaluación'


def reporte_experimental(evaluacion):
    partes = [evaluacion['reporte_base'], '\nPLAN DE TRATAMIENTO PIMS V3',
              'Evaluación: '+evaluacion['id'],
              'El análisis original se conserva. Las asignaciones y los estados son registros de revisión humana.',
              '\n| Código | Riesgo | Responsable | Plazo | Estado | Riesgo residual |',
              '| --- | --- | --- | --- | --- | --- |']
    for p in evaluacion['planes']:
        valores = [p['codigo'],p['riesgo'],p['responsable'] or 'Por asignar',
                   p['fecha_fin'] or 'Por acordar',p['estado'],residual(p)]
        partes.append('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in valores)+' |')
    for p in evaluacion['planes']:
        partes.extend(['\n'+p['codigo']+' · '+p['riesgo'], 'Hecho: '+p['hecho'],
                       'Medida vigente del plan: '+p['medida'], 'Verificación: '+p['verificacion'],
                       'Área: '+(p['area'] or 'Por asignar'), 'Versión del plan: '+str(p['version'])])
        partes.append('Fuentes cotejadas: '+('; '.join(x['tipo']+' '+x['codigo'] for x in p['referencias']) or 'Sin relación verificada'))
        for n,a in enumerate(p['actividades'],1):
            partes.append(f"Actividad {n}: {a['descripcion']} · Responsable: {a['responsable'] or 'Por asignar'} · Plazo: {a['fecha_fin'] or 'Por acordar'} · {'Completada' if a['completada'] else 'Pendiente'}")
        if p['evidencia_verificacion']:
            partes.extend(['Evidencia de verificación: '+p['evidencia_verificacion'],
                           'Verificado por: '+p['verificado_por'],
                           'Fecha de verificación: '+(p['fecha_verificacion'] or 'Pendiente')])
    return '\n'.join(partes)+'\n'


def exportar_csv(evaluacion):
    salida = io.StringIO(newline='')
    escritor = csv.writer(salida)
    escritor.writerow(['Código','Riesgo','Hecho','Amenaza','Vulnerabilidad','Medida','Verificación',
                       'Prioridad','Fuentes cotejadas','Responsable','Área','Inicio','Plazo','Estado',
                       'Actividades','Riesgo residual','Evidencia de verificación','Versión'])
    for p in evaluacion['planes']:
        valores = [p['codigo'],p['riesgo'],p['hecho'],p['amenaza'],p['vulnerabilidad'],p['medida'],
                   p['verificacion'],p['prioridad'],'; '.join(x['tipo']+' '+x['codigo'] for x in p['referencias']),
                   p['responsable'],p['area'],p['fecha_inicio'] or '',p['fecha_fin'] or '',p['estado'],
                   '; '.join(a['descripcion'] for a in p['actividades']),residual(p),p['evidencia_verificacion'],p['version']]
        escritor.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v for v in valores])
    return '\ufeff'+salida.getvalue()
