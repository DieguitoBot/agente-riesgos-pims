# Ensayo de la implementación de PIMS v3

Fecha: 3 de noviembre de 2026. Carpeta: `agente_riesgos_pims_v3`.

## Conservación del avance aprobado

Se tomó una copia de 46 archivos de referencia antes de implementar el
PIMS v3. La comprobación posterior encontró todos esos archivos iguales.
Las huellas de documentos, fragmentos y controles de la base aprobada también
coincidieron con las tomadas antes de copiar el corpus.

Se creó `pims_riesgos_experimental` en el clúster privado existente. El usuario
`pims_experimental_app` no tiene permiso de conexión a `pims_riesgos`, no puede
editar el corpus de su propia copia y no puede actualizar los resultados
originales guardados. Solo modifica el seguimiento experimental.

## Pruebas realizadas

| Prueba | Resultado |
| --- | --- |
| Suite propia dPIMS v3 | 22 pruebas aprobadas, incluidas 6 con PostgreSQL. |
| Suite de la versión aprobada | 93 pruebas descubiertas, 84 aprobadas y 9 omitidas por configuración. |
| Navegador real Chromium | Historial, apertura, edición, recarga, CSV y comparación comprobados. |
| Adaptación de tabla | Vistas de 1440, 900 y 390 píxeles sin desbordamiento horizontal. |
| Edición simultánea | La versión antigua del plan recibe conflicto en vez de sobrescribir. |
| Verificación y residual | Se rechazan estados verificados sin evidencia y cifras residuales incompletas. |
| Archivos y corpus aprobados | Huellas sin cambios. |
| Aplicaciones | La aprobada responde en 8080 y la experimental en 8180. |

Las seis pruebas de persistencia usan transacciones revertidas. Las pruebas de
navegador guardaron y restauraron valores de ensayo en un plan experimental;
las revisiones quedan registradas en `cambios`.

## Ensayo con Ollama real

Se envió `ejemplo_calidad_rag.json` a `POST /api/evaluar` de la aplicación
experimental. La respuesta fue HTTP 200 y la evaluación se guardó con:

- Tiempo del análisis: aproximadamente 238 segundos en este ensayo.
- 5 riesgos y 5 propuestas de plan, cada una con una actividad inicial pendiente.
- 4 referencias ISO, 2 legales y 4 RAG con citas cotejadas.
- 0 responsables inventados, 0 plazos inventados y 0 planes marcados como verificados.
- Resultado original y reporte base conservados sin cambios.

La actividad inicial reproduce la medida propuesta; no representa un desglose
automático validado de tareas ni una medida ya ejecutada. La persona revisora
puede dividirla en actividades, asignarlas y documentar su ejecución.

El JSON del ensayo no produjo alertas automáticas de coherencia. Esto no
acredita corrección de las inferencias ni pertinencia normativa de todas las
relaciones. El resultado mantiene el estado de borrador pendiente de revisión.

## Qué comparación es válida

Se puede descargar el reporte original y el ampliado de **la misma evaluación**.
Comparten exactamente el análisis de IA. El ampliado añade el plan tabulado,
sus campos de gestión y el estado vigente de seguimiento.

También se copió al historial la respuesta JSON del ensayo aprobado, con
procedencia `referencia_aprobada`. Esa referencia permite probar los campos
nuevos sobre una salida ya conocida, sin solicitar otra generación ni alterar
el archivo original.

No se concluye que la IA sea más precisa o más rápida. La mejora comprobada es
que el resultado queda guardado, se puede retomar y cada riesgo tiene un plan
editable con actividades, fuentes y revisión trazable. El modelo y el método
de recuperación documental se mantienen en la copia de esta versión.

## Evidencia local

La carpeta privada `datos/` contiene `base_verificada.json`,
`aislamiento_verificado.json`, `ensayo_ollama.json`, `resumen_ensayo.json`,
`prueba_navegador.json`, las capturas y los reportes y CSV del ensayo.
No se añaden estos resultados ni credenciales a Git.

## Preparación para compartir la rama

Se añadió una demostración ficticia independiente de las bases locales. Se
probó una copia limpia en `/tmp`, sin `.env`, documentos privados ni base
aprobada. La preparación creó su clúster y un caso manual con dos riesgos,
identificado como demostración sin IA. Las 23 pruebas pasaron, incluidas las
seis SQL. La demostración no aporta referencias normativas ni se presenta como
un análisis generado por el modelo.
