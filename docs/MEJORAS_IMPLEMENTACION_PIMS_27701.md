# Mejoras de implementación PIMS ISO/IEC 27701:2025 — tercera entrega

> Actualización de mantenimiento (24/11/2026): el estado «sin commits, push ni merge»
> describe únicamente el cierre de la validación anterior. El avance se guardó en
> `8f9dc59` y se incorporó a `main` mediante `53a886b` (PR #8).
> Esta fase parte de `53a886b` en `mantenimiento/ajustes-finales-pims-v3`,
> dentro de un worktree separado para preservar cambios locales pendientes.
> No se han publicado los cambios de mantenimiento. Los resultados históricos
> de este informe se conservan; véase [mantenimiento final](MANTENIMIENTO_FINAL_PIMS_V3.md).


## 1. Introducción

El Agente PIMS V3 apoya una simulación académica en matrícula, bienestar y biblioteca
de la UNSA. La tercera entrega consolida documentación, evaluación y reporte sin
reemplazar Flask, PostgreSQL, Ollama, planes, historial o recuperación híbrida.
No constituye una implantación institucional aprobada.

## 2. Objetivo de las mejoras

Cerrar la brecha entre tener archivos en una carpeta y utilizarlos como evidencia
versionada: incorporar la ISO ausente, revisar sistemáticamente la SoA, estructurar
reportes y demostrar el funcionamiento real. Se preservan métodos y registros existentes.

## 3. Arquitectura documental

Los archivos privados/autorizados se usan únicamente para incorporación. Mantenimiento
extrae texto, metadatos y fragmentos; PostgreSQL conserva originales, fuentes vigentes,
versiones y vectores. Durante HTTP, el agente consulta PostgreSQL. Python determina
cifras/prioridad; Ollama interpreta el contexto; validadores cotejan citas; el reporte
se genera sin otra llamada al modelo. Los planes editables están separados del
análisis original y conservan versiones y bitácora.

## 4. Uso de PostgreSQL

Base exclusiva `pims_riesgos_experimental`, por socket Unix privado. La aplicación
mantiene privilegios limitados. Se examinó el inventario antes de importar y se
comprobó que el SHA de la ISO no estaba registrado. La actualización selectiva
procesó solo tres fuentes y se repitió sin duplicar documentos. Permanecen intactas
las 23 evaluaciones anteriores, comprobadas mediante hashes de JSON y reporte.

Estado final: 29 documentos, 2.428 fragmentos, 2.302 vectores y 12 revisiones archivadas.
Los artículos/secciones tipados se recuperan además por su vía específica. El
duplicado heredado de Ley 29733 se conserva por sus dos representaciones; no se
introdujo una restricción global por SHA que rompiera rutas o referencias existentes.

## 5. Integración del RAG

Se mantiene BM25 más similitud coseno de embeddings locales. La ISO ahora aporta
86 secciones y 120 fragmentos semánticos, incluidos 6.1.3 y las tablas A. Se corrige
la identificación derivada de B.14.4 y se registra la limitación sin alterar la fuente.
La separación evita atribuir su contenido a B.1.4.3. Los metadatos incluyen categoría,
versión, SHA, página/línea, sección y localizador; las fuentes antiguas siguen cotejables.

Se consultaron metodología, matriz, SoA, plan e inventarios, además de ISO 6.1.3 y
B.3.9. Las ocho consultas específicas recuperaron su objetivo y los diez PIMS
se recuperaron individualmente. La consulta institucional adicional recuperó el
estatuto, ROF, RCU, mapa, MOF y política con su procedencia. Los archivos locales no son un respaldo silencioso
de consultas cuando PostgreSQL falla.

## 6. Documentos utilizados

Norma ISO privada OCR autorizada; Ley 29733 aportada con limitaciones de actualización;
ocho fuentes registradas como institucionales; y PIMS-RIE-01, 02, 03, 03A, 04,
05A, 05B, 06, 07 y 21. PIMS-RIE-04 y 06 avanzaron a 0.3. La norma mantiene SHA
`3ebb2f46b928d3a82570cb9cba8cb4bcd1ab5f632fbb24929c1507a58b3a717f` y queda fuera de Git. No se copiaron plantillas licenciadas del docente.

## 7. Revisión de SoA

La SoA 0.3 incluye 78 registros: 31 de A.1, 18 de A.2 y 29 de A.3. Se documentan
nombre resumido propio, decisión, justificación, riesgos, estado, evidencia, acción,
observaciones y fuente. Hay 11 inclusiones propuestas, 49 decisiones pendientes y
18 pendientes de rol encargado. No hay exclusiones definitivas sin fundamento ni
controles declarados implementados por redactar un documento.

Se preservan las relaciones RIE/TRA/ACT/ACC existentes. Se amplía la revisión a
registros, finalidad, base jurídica, EIPD, políticas y trazas. Las acciones no
programadas y los propietarios/plazos desconocidos quedan pendientes. Esta es una
revisión sistemática con decisiones abiertas; no se presenta como SoA real completa.

## 8. Mejoras en los reportes

PIMS-RIE-06 revisión 0.3 define los 26 campos solicitados y el formato dinámico 1.0.
El generador incorpora estructura propia, encabezado de simulación, UUID/fecha,
resumen, alcance, datos/activos, método, riesgos, controles/estado SoA, plan y residual,
evidencias, conclusiones, recomendaciones y límites. Datos faltantes se identifican,
sin inventar responsables, plazos, reducciones o aprobación.

Se distingue el cálculo Python de la opinión IA y de la evidencia documental.
TXT/base y CSV se conservan; CSV amplía trazabilidad sin retirar columnas previas.
HTML se añade por su utilidad concreta para impresión A4 y revisión académica,
con tablas, jerarquía, estados y referencias agrupadas. El PDF comprobado se obtiene
con la función de impresión del navegador. Las claves de API y reportes originales
se conservan para mantener compatibilidad e historial.

## 9. Justificación técnica

Los cambios se limitan a carencias observadas: OCR omitido, cláusulas/tablas ausentes,
SoA parcial, falta de identificación y estructura en reportes, y procedencia incompleta.
Se conserva el esquema de evaluación P × I y sus bandas; el modelo no sobrescribe
resultados. El contexto por defecto aumenta a 32.768 para alojar normativa y SoA;
las variables existentes prevalecen y `.env` no se reescribe.

Los generadores de documentos preservan copia privada y evitan cambios de huella
si el contenido no varía. Las utilidades de edición DOCX y navegador son opcionales.
No se agregaron FAISS, una base paralela, servicios externos de IA ni exportadores
PDF del servidor. Los enlaces por SHA y el archivo documental conservan trazabilidad.

Archivos principales del conjunto consolidado:

| Área | Archivos | Propósito |
|---|---|---|
| Persistencia | `db/migrar.py`, `db/repositorio.py`, esquema/administración existentes | Incorporación selectiva, procedencia y versiones |
| Normativa y SoA | `knowledge/documento_iso.py`, `controles_iso.py`, `revision_soa.py`, `documento_pims.py` | OCR, 78 controles y decisiones documentales |
| Recuperación | `rag/documentos.py`, `rag/recuperar_contexto.py` | DOCX/ISO, límites de fragmento y selección contextual |
| Evaluación | `skills/evaluacion_riesgo.py`, `prompts/riesgo_prompt.py`, `knowledge/evidencia_rag.py` | Identidad, SoA, citas y separación cálculo/interpretación |
| Reportes/API | `skills/reporte.py`, `experimento.py`, `app.py` | Estructura, persistencia compatible y exportación |
| Presentación | `templates/reporte.html`, `templates/index.html`, `static/css/style.css`, ambos JS | Impresión y visualización de resultados |
| Herramientas | `mantenimiento/*.py`, `validar_pims.py`, `pruebas_consolidacion_visual.py`, `requirements-validacion.txt` | Autoría, auditoría, casos reales y navegador |
| Verificación | `tests/test_consolidacion.py`, pruebas PIMS y revisión existentes, `tests_experimento.py` | Regresiones y SQL real |
| Operación | `config.py`, README/RAG y estos informes | Presupuesto de contexto y reproducción |

## 10. Justificación normativa

La revisión utiliza la fuente autorizada disponible, especialmente 6.1.3 y la
correspondencia entre tablas A.1/A.2/A.3 y guías B. Se consideran controles necesarios,
justificaciones, estado, programa de seguridad, plan, aprobación y aceptación residual.
La escala académica es una decisión metodológica, no una fórmula atribuida a ISO.

La fuente es OCR: tablas A y enumeraciones requieren cotejo con PDF. No se inventan
requisitos legibles a partir de códigos corruptos. Se mantienen guías y localizadores
reales y se señalan las decisiones que no pueden cerrarse con el alcance disponible.
Las citas literales prueban procedencia, no cumplimiento o interpretación correcta.

## 11. Pruebas realizadas

```text
suite-final.log
----------------------------------------------------------------------
Ran 109 tests in 118.736s

OK
```

```text
suite-experimento.log
----------------------------------------------------------------------
Ran 23 tests in 0.072s

OK
```

Cinco evaluaciones HTTP con PostgreSQL y Ollama reales, IA obligatoria, cero mocks de
modelo en esos POST; verificación de citas contra SQL y endpoints; indexación real;
idempotencia; hashes históricos; exportaciones; navegador Chromium en 1440/900/390,
edición/restauración de un plan nuevo y PDF real. El formulario del navegador
reproduce una respuesta real guardada; se informa separadamente de los cinco POST
que sí generaron IA nueva. No se fabricaron capturas o resultados.

## 12. Comparación de resultados

| Caso | Entrada idéntica | Puntaje antes/después | ISO antes/después | Tiempo antes/después |
|---|---|---:|---:|---:|
| 1 | Sí | 12 / 12 | 0 / 1 | 39.39 / 77.88 s |
| 2 | Sí | 16 / 16 | 0 / 2 | 85.68 / 125.87 s |
| 3 | Sí | 15 / 15 | 0 / 1 | 96.53 / 130.06 s |
| 4 | Sí | 9 / 9 | 0 / 2 | 47.57 / 120.16 s |
| 5 | Sí | 20 / 20 | 0 / 3 | 89.11 / 154.69 s |

La ISO no estaba antes en la base; ahora los cinco casos producen 9 referencias
ISO cotejadas. Los puntajes permanecen iguales. Las nuevas fuentes, SoA y contexto
cambian las condiciones: no se atribuye causalmente una mejora semántica o de
latencia al cambio de formato. Las latencias nuevas son mayores en parte de la muestra.
Persisten inferencias que requieren revisión humana; las alertas se conservan.

La comparación de formato sí se aisló: ambos generadores recibieron el mismo
análisis congelado y las mismas fuentes, sin nueva IA:

| Campo medido con el mismo análisis congelado | Formato anterior | Formato nuevo |
|---|---:|---:|
| identificador | 0/5 | 5/5 |
| version formato | 0/5 | 5/5 |
| encabezado academico | 0/5 | 5/5 |
| resumen ejecutivo | 0/5 | 5/5 |
| objetivo alcance | 0/5 | 5/5 |
| conclusiones | 0/5 | 5/5 |

## 13. Evidencias obtenidas

| Caso | P × I | Nivel | Tiempo real | Citas ISO / ley / RAG | Alertas |
|---|---|---|---:|---:|---:|
| 1. Acceso no autorizado a expedientes académicos | 3 × 4 = 12 | Alto | 77.88 s | 1 / 2 / 2 | 3 |
| 2. Exposición durante matrícula | 4 × 4 = 16 | Alto | 125.87 s | 2 / 2 / 2 | 3 |
| 3. Acceso a bienestar | 3 × 5 = 15 | Alto | 130.06 s | 1 / 3 / 4 | 1 |
| 4. Conservación excesiva | 3 × 3 = 9 | Medio | 120.16 s | 2 / 1 / 2 | 0 |
| 5. Divulgación a terceros | 4 × 5 = 20 | Crítico | 154.69 s | 3 / 3 / 4 | 1 |

Cada UUID coincide con el reporte guardado y puede abrirse en el historial.
`datos/consolidacion/` contiene auditoría de solo lectura, registros de pruebas,
entradas/respuestas exactas, exportaciones, capturas y PDF. La conservación de
23 evaluaciones se verificó antes/después de la incorporación y otra vez al cierre.
Los informes públicos contienen conteos, códigos, decisiones propias y hashes;
la norma íntegra y los artefactos de ejecución permanecen privados e ignorados.

## 14. Limitaciones

Cotejo OCR con PDF, 67 decisiones SoA, roles, bases jurídicas y datos reales de
alcance; evidencias operativas y aprobación humana; revisión Word de la tabla A3;
y evaluación semántica experta del LLM. Ni las pruebas ni las citas acreditan
implantación real en la UNSA, conformidad completa, eficacia de controles o aceptación
residual. No se presume que una fuente institucional antigua esté vigente.

## 15. Conclusiones

La consolidación técnica está probada: PostgreSQL sigue siendo el repositorio
central; la ISO se incorporó una sola vez con trazabilidad; la SoA fue revisada
sistemáticamente; y los reportes presentan una estructura propia verificable.
Se mantuvieron cálculo, planes, historial y exportaciones. La mejora de estructura
y disponibilidad normativa está medida; una mejora general de razonamiento del LLM
no está demostrada. La tercera entrega debe presentarse como simulación académica
con decisiones y validaciones humanas pendientes.

Para reproducir comandos, versiones, casos y resultados completos, consultar
[la validación documental](VALIDACION_DOCUMENTAL_PIMS_27701.md). Al cierre de aquella
validación no se habían hecho commits, push, merge ni cambios en `main`; el estado
posterior se aclara al inicio de este informe.
