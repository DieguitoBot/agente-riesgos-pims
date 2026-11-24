"""Revisión académica del alcance; resúmenes propios, sin reproducir requisitos ISO.

El universo se coteja con las guías B del OCR privado. Las decisiones y vínculos
son propuestas de este proyecto; no constituyen aprobación de la UNSA.
"""
GRUPOS = {
 'A.1.2': (2, ['Finalidad del tratamiento','Base de legitimación','Criterios para solicitar consentimiento',
              'Registro del consentimiento','Evaluación de impacto','Contratos con encargados',
              'Corresponsabilidad','Registro de tratamientos del responsable']),
 'A.1.3': (2, ['Obligaciones frente a titulares','Información que se comunica al titular','Comunicación al titular',
              'Modificar o retirar consentimiento','Oposición al tratamiento','Acceso, corrección y supresión',
              'Avisos a terceros sobre cambios','Entrega de copia de datos','Atención de solicitudes','Decisiones automatizadas']),
 'A.1.4': (2, ['Limitación de la recogida','Limitación del tratamiento','Exactitud y calidad','Objetivos de minimización',
              'Desidentificación y eliminación al finalizar','Archivos temporales','Conservación','Disposición','Protección en transmisión']),
 'A.1.5': (2, ['Fundamento de transferencias internacionales','Destinos internacionales','Registro de transferencias','Registro de divulgaciones']),
 'A.2.2': (2, ['Acuerdo con el cliente','Finalidades del encargado','Uso para publicidad','Instrucciones incompatibles',
              'Apoyo al cliente','Registro de tratamientos del encargado']),
 'A.2.3': (2, ['Apoyo a derechos de titulares']),
 'A.2.4': (2, ['Archivos temporales del encargado','Devolución o eliminación','Transmisión del encargado']),
 'A.2.5': (2, ['Fundamento de transferencias del encargado','Destinos del encargado','Registro de divulgaciones del encargado',
              'Aviso de solicitudes de divulgación','Divulgaciones obligatorias','Identificación de subencargados',
              'Contratación de subencargados','Cambios de subencargados']),
 'A.3': (3, ['Políticas de seguridad','Roles de seguridad','Clasificación de información','Etiquetado de información',
            'Transferencia de información','Gestión de identidades','Permisos de acceso','Seguridad en acuerdos con proveedores',
            'Preparación para incidentes','Respuesta a incidentes','Requisitos legales y contractuales','Protección de registros',
            'Revisión independiente','Revisión de políticas de seguridad','Sensibilización y formación','Confidencialidad',
            'Protección de puestos y pantallas','Medios de almacenamiento','Disposición de equipos','Dispositivos de usuario',
            'Autenticación segura','Respaldos','Registro de eventos','Criptografía','Seguridad del ciclo de desarrollo',
            'Requisitos de seguridad de aplicaciones','Arquitectura segura','Desarrollo externo','Datos de prueba']),
}
CATALOGO = {f'{prefijo}.{inicio+n}': nombre for prefijo,(inicio,nombres) in GRUPOS.items() for n,nombre in enumerate(nombres)}

# Solo vinculaciones sustentadas en los escenarios, registros y acciones entregados.
INCLUSIONES = {
 'A.3.5': ('RIE-002','ACC-003','La clasificación permite delimitar acceso al expediente de bienestar.'),
 'A.3.8': ('RIE-001','ACC-001','La revisión de perfiles requiere identidades individualizadas.'),
 'A.3.9': ('RIE-001; RIE-002','ACC-001; ACC-003','Los riesgos declarados provienen de permisos excesivos.'),
 'A.3.25': ('RIE-001','ACC-002','El plan propone registrar y revisar accesos para su trazabilidad.'),
 'A.1.4.8': ('RIE-003','ACC-005','La conservación prolongada exige evaluar plazos según finalidad y fundamento.'),
 'A.1.4.9': ('RIE-003','ACC-005','La acción de retención contempla eliminación verificable.'),
 'A.1.2.6': ('RIE-002','ACC-004','El supuesto de bienestar justifica decidir y documentar si procede ampliar la EIPD.'),
 'A.1.2.9': ('RIE-001; RIE-002; RIE-003','Completar PIMS-RIE-05B; programación pendiente',
              'El registro existe como borrador y requiere completar roles, bases, destinatarios y plazos.'),
 'A.1.2.2': ('RIE-001; RIE-002; RIE-003','Revisar PIMS-RIE-05B; programación pendiente',
              'Los tres tratamientos necesitan finalidades delimitadas antes de evaluar usos secundarios.'),
 'A.1.2.3': ('RIE-001; RIE-002; RIE-003','Completar PIMS-RIE-05B; programación pendiente',
              'Las bases jurídicas no constan; se propone documentarlas sin presuponer consentimiento universal.'),
 'A.3.3': ('RIE-001; RIE-002; RIE-003','Programa de seguridad por planificar',
           'Se propone documentar políticas y programa de seguridad coherentes con el tratamiento de riesgos.'),
}


def decision(codigo):
    if codigo.startswith('A.2.'):
        return ('Pendiente de rol', 'TRA-001/002/003 se describen como responsable por confirmar; '
                'no hay operación como encargado documentada. No se declara exclusión definitiva; '
                'reevaluar si se procesa por cuenta de un cliente.')
    if codigo in INCLUSIONES:
        return 'Incluido propuesto', INCLUSIONES[codigo][2]
    criterios = {
      'A.1.2.4':'Determinar primero la base jurídica y si corresponde solicitar consentimiento.',
      'A.1.2.5':'No constan mecanismos de consentimiento ni su necesidad jurídica por tratamiento.',
      'A.1.2.7':'No constan proveedores encargados; verificar contratos y obligaciones antes de decidir.',
      'A.1.2.8':'No se documentan corresponsables; confirmar finalidades y medios compartidos.',
      'A.1.3.11':'No se documentan decisiones automatizadas; confirmar si existen y sus efectos.',
      'A.1.4.4':'No hay mediciones de exactitud; evaluar daño e integridad sin inventar incidentes.',
      'A.1.4.5':'Definir métricas y objetivos de minimización; no existen mediciones operativas.',
      'A.1.4.6':'Evaluar desidentificación al concluir finalidad; no presumir anonimización eficaz.',
      'A.1.4.7':'Confirmar existencia y ciclo de vida de copias temporales; no hay inventario técnico.',
      'A.1.4.10':'Los flujos de 05A son hipotéticos; verificar canales y destinatarios efectivos.',
      'A.3.7':'Los flujos propuestos requieren validar destinatarios, autorizaciones y canales.',
      'A.3.23':'El riesgo documentado es de permisos; confirmar autenticación antes de atribuir una carencia.',
      'A.3.24':'Confirmar necesidades de recuperación y ensayos; no constan copias ni su ausencia.',
      'A.3.26':'Evaluar protección en tránsito y reposo; no existe inventario criptográfico verificable.',
      'A.3.10':'Confirmar proveedores, servicios y obligaciones; no inventar contratos.',
      'A.3.30':'No consta desarrollo contratado; verificar alcance antes de justificar exclusión.',
    }
    if codigo in criterios:
        return 'Pendiente de decisión', criterios[codigo]
    if codigo.startswith('A.1.3.'):
        return 'Pendiente de decisión', 'Evaluar obligaciones y procedimientos de derechos en los tres tratamientos; faltan canales, plazos y evidencia operativa.'
    if codigo.startswith('A.1.5.'):
        return 'Pendiente de decisión', '05B no define destinatarios ni transferencias; confirmar jurisdicciones y registros. Ausencia de datos no justifica exclusión.'
    return 'Pendiente de decisión', ('Evaluar '+CATALOGO[codigo].lower()+
        ' según activos, personas, contratos y ciclo de vida reales. El inventario simulado no permite decidir ni justificar una exclusión definitiva.')


def revisar(secciones, huella):
    faltantes = [c for c in CATALOGO if 'B'+c[1:] not in secciones]
    if faltantes:
        raise ValueError('Guías no reconocidas en la fuente privada: '+', '.join(faltantes))
    filas=[]
    for codigo,nombre in CATALOGO.items():
        guia=secciones['B'+codigo[1:]];aplicabilidad,justificacion=decision(codigo)
        vinculo=INCLUSIONES.get(codigo)
        filas.append(dict(codigo=codigo,nombre=nombre,aplicabilidad=aplicabilidad,justificacion=justificacion,
            riesgos=vinculo[0] if vinculo else 'Vínculo específico pendiente de análisis',
            estado='Propuesto; no implementado acreditado' if vinculo else 'No evaluado operativamente',
            evidencia='Documentos simulados 02/03/05A/05B/21; sin evidencia operativa' if vinculo else 'No aportada',
            acciones=vinculo[1] if vinculo else 'Pendiente de definir; sin aprobación',
            observaciones=('Rol responsable supuesto, por confirmar. ' if codigo.startswith('A.1.') else
                           'Rol encargado no confirmado. ' if codigo.startswith('A.2.') else 'Control transversal; alcance por confirmar. ')
                          +'Tabla A afectada por OCR: cotejo PDF pendiente. Decisión sin aprobación institucional.',
            fuente=f"ISO/IEC 27701:2025 · B{codigo[1:]} · página OCR {guia['pagina']} · línea {guia['linea']} · SHA256 {huella}"))
    return filas
