"""Ejemplo ficticio para probar el seguimiento sin IA ni documentos privados."""
def crear_resultado_demo():
    descripcion = ('CASO FICTICIO DE DEMOSTRACIÓN. Una organización comparte una lista de contactos '
                   'mediante un enlace público y conserva los registros sin plazo definido.')
    riesgos = [
        dict(riesgo='Exposición de contactos por enlace público', evidencia='enlace público',
             explicacion='Ejemplo preparado manualmente para probar la tabla; no es un análisis de IA.',
             amenaza='Consulta del enlace por terceros', vulnerabilidad='Permisos de lectura públicos',
             dano_personas='Divulgación de los datos de contacto', medida_concreta='Restringir el enlace a usuarios autorizados.',
             verificacion='Comprobar que una cuenta sin permiso no puede abrir el enlace.', prioridad='alta'),
        dict(riesgo='Conservación sin plazo definido', evidencia='conserva los registros sin plazo definido',
             explicacion='Ejemplo preparado manualmente para probar actividades y plazos.',
             amenaza='Acceso posterior a registros conservados', vulnerabilidad='Ausencia declarada de plazo de conservación',
             dano_personas='Exposición prolongada de datos', medida_concreta='Definir y revisar un plazo de conservación justificado.',
             verificacion='Revisar el calendario aprobado y registrar una prueba de eliminación.', prioridad='media')]
    aviso='Demostración con datos ficticios, sin generación de IA ni referencias normativas.'
    doc=dict(estado='demostracion',sha256=None,mensaje=aviso)
    return dict(descripcion=descripcion,probabilidad=4,impacto=4,puntaje=16,nivel='Alto',
                categorias=['Contacto'],rol_privacidad='responsable',modelo='sin-ia-demo',
                modo='demostracion',llm_disponible=False,reporte_ia_generado=False,formato_ia=None,
                mensaje=aviso,valoracion_ia=None,estado_revision='demostracion_sin_ia',
                alertas_contenido=[],avisos_revision=[aviso],indicadores_riesgo=[],
                riesgos_identificados=[r['riesgo'] for r in riesgos],
                consecuencias=['Posible divulgación de datos en este caso ficticio.'],
                justificacion='Valoración ilustrativa calculada como 4 × 4; requiere revisión en un caso real.',
                recomendaciones=['Revisar los permisos y los plazos del ejemplo.'],
                analisis_ia=dict(riesgos_identificados=riesgos,consecuencias=['Posible divulgación de datos.']),
                documentacion_iso=dict(doc,secciones=[]),documentacion_ley=dict(doc,articulos=[]),
                referencias_iso=[],referencias_ley=[],referencias_rag=[],fuentes_rag=[],estado_rag=aviso,
                reporte_texto='DEMOSTRACIÓN SIN IA — DATOS FICTICIOS\n'+descripcion+'\n'+aviso+'\n')
