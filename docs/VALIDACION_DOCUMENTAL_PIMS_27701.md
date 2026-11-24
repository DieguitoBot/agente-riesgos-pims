# Validación final de consolidación PIMS V3 — 23/11/2026

**Implementación académica simulada. Sin aprobación institucional de la UNSA.**
La integración y los cotejos técnicos fueron ejecutados; no certifican cumplimiento,
implementación operativa ni corrección semántica completa de las inferencias del LLM.

## 1. Alcance y estado previo

Rama: `trabajo/expediente-privacidad-unsa`. HEAD conservado:
`2ad8ad8316f62086d343a28329e5f9bc05e5e8d4`. Sin commits, push ni merge.
Se conservaron las modificaciones previas y la arquitectura V3. La auditoría inicial
confirmó 28 documentos, 2.114 fragmentos, 2.074 vectores, 23 evaluaciones y ninguna
ISO registrada. El archivo privado recién aportado sí existía en la raíz; su hash
no aparecía en PostgreSQL. Se comprobó antes de importar.

La validación anterior y las cinco respuestas previas se conservaron en
`agente_riesgos_pims_v3/datos/consolidacion_antes/` antes de actualizar este informe.

## 2. Entorno utilizado y configuración

Ubuntu, Python 3.10.12, Flask 3.1.2 y PostgreSQL 14.24. Entorno `.venv/` propio de V3.
`.env` no se sobrescribió; continúa privado. Base: `pims_riesgos_experimental`,
socket Unix `datos/socket_demo`, puerto lógico 55440 sin TCP. La aplicación usa el
rol limitado; la importación usa la conexión administrativa solo en mantenimiento.

Ollama local y modelos existentes `qwen3.5:4b-q4_K_M` y `embeddinggemma`.
No se descargaron modelos. El contexto predeterminado pasó de 16.384 a 32.768 tokens
para alojar normativa, SoA y fuentes; una variable explícita del entorno prevalece.
Los presupuestos siguen validados. Se instalaron herramientas opcionales de edición
DOCX y Playwright; Chromium de pruebas se descargó en `/tmp/pims-browsers`.

## 3. Estado real de PostgreSQL

| Grupo lógico | Documentos vigentes | Fragmentos | Vectores |
|---|---:|---:|---:|
| Normativa | 3 | 297 | 171 |
| Institucional | 8 | 1.877 | 1.877 |
| Implementación PIMS | 10 | 254 | 254 |
| Otros documentos del proyecto | 8 | 0 | 0 |
| **Total** | **29** | **2.428** | **2.302** |

PIMS se almacena físicamente como `proyecto`; la separación lógica proviene de sus
metadatos. Los 126 fragmentos sin vector corresponden a 86 secciones ISO y 40
artículos legales de recuperación específica. Sus copias para búsqueda RAG tienen
vectores. No son 126 fallos de indexación.

Persisten los ocho institucionales: MOF-2005-TOMO-I/II, RCU-0103-2026-1,
RCU-0306-2022-ROF-Organigrama-1, estatuto, mapa de procesos, plan de tratamiento y
política de privacidad. Su clasificación almacenada no acredita vigencia u origen
oficial; esos metadatos siguen pendientes de validación. No se los modificó.

## 4. Documentos PIMS incorporados y actualizados

| Documento PIMS | Versión almacenada | Fragmentos / vectores |
|---|---|---:|
| PIMS-RIE-01 | 0.2 — documento académico para revisión | 22 / 22 |
| PIMS-RIE-02 | 0.2 — documento académico para revisión | 14 / 14 |
| PIMS-RIE-03A | 0.2 — documento académico para revisión | 10 / 10 |
| PIMS-RIE-03 | 0.1 — documento académico para revisión | 16 / 16 |
| PIMS-RIE-04 | 0.3 — revisión académica sistemática | 95 / 95 |
| PIMS-RIE-05A | 0.1 · borrador académico | 12 / 12 |
| PIMS-RIE-05B | 0.1 · borrador académico | 12 / 12 |
| PIMS-RIE-06 | 0.3 — formato académico para revisión | 49 / 49 |
| PIMS-RIE-07 | 0.1 · borrador académico | 12 / 12 |
| PIMS-RIE-21 | 0.1 · borrador académico | 12 / 12 |

Se actualizaron únicamente SoA y formato de informe, ambos a 0.3. Los códigos y
los identificadores SQL existentes se conservaron. Los DOCX anteriores tienen
copias locales privadas y las versiones sustituidas están archivadas en PostgreSQL.

## 5. ISO autorizada, extracción e incidencias OCR

La fuente local permanece intacta, ignorada por Git, con SHA-256
`3ebb2f46b928d3a82570cb9cba8cb4bcd1ab5f632fbb24929c1507a58b3a717f`. Está registrada una sola vez. Su texto completo y sus bytes
originales permanecen en PostgreSQL, sin convertir los archivos locales en un
repositorio de consulta paralelo.

Se extrajeron 86 secciones: 4.3, 6.1.2, 6.1.3, 8.2, 8.3, tablas A.1/A.2/A.3 y 78
guías B. Se añadieron 120 fragmentos RAG de esas secciones. El registro ISO tiene
206 fragmentos en total y 120 vectores.

Incidencias detectadas: códigos deteriorados en las tablas A, enumeración dañada
al final de 6.1.3 y encabezado `B.14.4` en la línea 2143. Este último se identifica
como B.1.4.4 por título, secuencia y correspondencia; la corrección se registra en
metadatos y se conserva el texto OCR literal. Antes se omitía y su contenido podía
quedar unido a B.1.4.3. La prueba de separación utiliza texto sintético.

Las tablas A se conservan completas con localizadores; no se fabricaron renglones
normativos individuales desde sus identificadores ilegibles. Los controles se
corroboran por la correspondencia A/B declarada por la fuente. **El cotejo con PDF
autorizado sigue pendiente**: no se afirma que todo el OCR esté corregido.

## 6. SoA 0.3: revisión sistemática y decisiones

Se revisaron 78 controles: A.1 contiene 31, A.2 contiene 18 y A.3 contiene 29.
Cada fila incluye código, resumen propio, aplicabilidad, justificación, riesgos,
estado, evidencia, acción, observaciones y localizador de fuente.

- 11 inclusiones propuestas, vinculadas a riesgos/registros/acciones conocidos.
- 49 decisiones pendientes de datos suficientes.
- 18 pendientes de confirmar operaciones como encargado.
- Cero exclusiones definitivas inventadas y cero implementaciones acreditadas.

La revisión considera 6.1.3: opciones, controles necesarios, programa de seguridad,
contraste con A, SoA con justificaciones/estados, plan, aprobación del propietario,
aceptación residual y orientaciones B. Los cinco controles iniciales se conservan;
se agregan propuestas justificadas de finalidad, base jurídica, registros, impacto,
políticas y trazas. Las acciones aún no programadas se indican como tales.

La cobertura de revisión es sistemática; **la SoA sigue siendo un borrador con
67 decisiones abiertas**, roles por confirmar y cotejo OCR pendiente. No se la
presenta como SoA institucional completa o aprobada. Su diseño Word utiliza A3
apaisado para las diez columnas; queda revisión manual en un editor Word.

## 7. Recuperación RAG y trazabilidad

| Consulta objetivo | Resultado real |
|---|---|
| `6.1.3` · ISO 6.1.3 privacy risk treatment statement applicability | Fuente objetivo recuperada |
| `B.3.9` · ISO Annex B B.3.9 access rights | Fuente objetivo recuperada |
| `PIMS-RIE-01` · PIMS-RIE-01 metodología evaluación riesgos | Fuente objetivo recuperada |
| `PIMS-RIE-02` · PIMS-RIE-02 matriz permisos RIE-001 | Fuente objetivo recuperada |
| `PIMS-RIE-04` · PIMS-RIE-04 declaración aplicabilidad controles propuestos | Fuente objetivo recuperada |
| `PIMS-RIE-03` · PIMS-RIE-03 plan tratamiento ACC-005 | Fuente objetivo recuperada |
| `PIMS-RIE-05A` · PIMS-RIE-05A inventario activos flujos | Fuente objetivo recuperada |
| `PIMS-RIE-05B` · PIMS-RIE-05B registro tratamientos | Fuente objetivo recuperada |

También se recuperaron individualmente los diez documentos PIMS. Una consulta
institucional adicional recuperó el estatuto, ROF/organigrama, RCU, mapa de
procesos, MOF y política de privacidad, conservando su categoría institucional. La búsqueda usa
BM25 y similitud coseno con embeddings locales almacenados en PostgreSQL. Se
conservan categoría, versión, SHA, sección, página/línea y localizador. Para una
evaluación se reservan criterios de PIMS-RIE-01 y un fragmento de 6.1.3, etiquetados
por su propósito sin fingir puntajes. Los IDs explícitos filtran filas ajenas de la
matriz; esto no sustituye revisión semántica.

Una cita ISO se verifica contra la guía recuperada y el hecho del escenario. La
SoA aporta su decisión/justificación/estado, sin transformar un candidato en un
control implementado. Los enlaces por SHA permiten consultar versiones archivadas.

## 8. Ejecución real de Flask y cinco escenarios

Instancia independiente iniciada con `bash iniciar.sh --sin-navegador --port 8185`.
URL validada: `http://127.0.0.1:8185`. No se detuvieron instancias del usuario en
otros puertos. Reiniciar cualquier instancia anterior es necesario para que cargue
el código actualizado. Estado, inicio, inventario, historial y recursos estáticos
respondieron HTTP 200; entradas/ediciones inválidas dieron 400 y fuente inexistente,
404. Los cinco POST usaron IA obligatoria, sin mocks de Ollama.

| Caso | P × I | Nivel | Tiempo real | Citas ISO / ley / RAG | Alertas |
|---|---|---|---:|---:|---:|
| 1. Acceso no autorizado a expedientes académicos | 3 × 4 = 12 | Alto | 77.88 s | 1 / 2 / 2 | 3 |
| 2. Exposición durante matrícula | 4 × 4 = 16 | Alto | 125.87 s | 2 / 2 / 2 | 3 |
| 3. Acceso a bienestar | 3 × 5 = 15 | Alto | 130.06 s | 1 / 3 / 4 | 1 |
| 4. Conservación excesiva | 3 × 3 = 9 | Medio | 120.16 s | 2 / 1 / 2 | 0 |
| 5. Divulgación a terceros | 4 × 5 = 20 | Crítico | 154.69 s | 3 / 3 / 4 | 1 |

Cada caso produjo reportes base, TXT con plan, CSV y HTML. Los IDs de evaluación
coincidieron entre JSON, reporte y fila SQL. Los planes permanecen propuestos,
sin aceptación residual ni responsables/plazos institucionales inventados. Python
conserva puntaje/nivel y prioridad alta para Altos/Críticos.

### Caso 1: Acceso no autorizado a expedientes académicos

Entrada exacta: Caso ficticio TRA-001 / ACT-001 / RIE-001: el sistema de matrícula permite acceso a expedientes académicos por permisos excesivos de cuentas de prueba. No consta revisión de permisos.

Identificador compartido por API/reporte/SQL: `b482a17f-8c39-4365-804f-ac2c2d714289`.

Controles ISO relacionados y cotejados: A.3.9 (Incluido propuesto).

Primera medida propuesta: Implementar un proceso de revisión de perfiles de usuario para asegurar que los permisos se ajustan al principio de mínimo privilegio. Esto implica definir roles específicos y retirar accesos no necesarios.

Resultado: HTTP 200, cálculo correcto, citas verificadas y exportaciones base/TXT/CSV/HTML. 3 alertas de contenido conservadas.

### Caso 2: Exposición durante matrícula

Entrada exacta: Caso ficticio TRA-001: una hoja de matrícula con nombres y correos de estudiantes de prueba está expuesta mediante un enlace público. Se requiere restringir la publicación.

Identificador compartido por API/reporte/SQL: `183230e2-550a-402a-afb5-d12f757ac8d2`.

Controles ISO relacionados y cotejados: A.3.7 (Pendiente de decisión); A.3.9 (Incluido propuesto).

Primera medida propuesta: Eliminar el enlace público de la hoja de matrícula. Restringir el acceso al activo mediante autenticación o eliminación del activo si no es necesario para el proceso académico.

Resultado: HTTP 200, cálculo correcto, citas verificadas y exportaciones base/TXT/CSV/HTML. 3 alertas de contenido conservadas.

### Caso 3: Acceso a bienestar

Entrada exacta: Caso ficticio TRA-002 / ACT-002 / RIE-002: cuentas de prueba sin autorización acceden a expedientes de bienestar con datos socioeconómicos y de salud ficticios por permisos excesivos.

Identificador compartido por API/reporte/SQL: `8a76b494-4976-4c9a-bf77-b9460e137e11`.

Controles ISO relacionados y cotejados: A.3.9 (Incluido propuesto).

Primera medida propuesta: Revisar y retirar permisos de acceso a cuentas de prueba; implementar revisión de perfiles de usuario; clasificar información sensible; realizar evaluación de impacto de privacidad.

Resultado: HTTP 200, cálculo correcto, citas verificadas y exportaciones base/TXT/CSV/HTML. 1 alertas de contenido conservadas.

### Caso 4: Conservación excesiva

Entrada exacta: Caso ficticio TRA-003 / ACT-003 / RIE-003: el historial de préstamos de estudiantes de prueba se conserva por tiempo indefinido, sin plazo ni eliminación definida.

Identificador compartido por API/reporte/SQL: `2b1b926b-42fd-4a15-a398-ad10ed4e7659`.

Controles ISO relacionados y cotejados: A.1.4.8 (Incluido propuesto); A.1.4.9 (Incluido propuesto).

Primera medida propuesta: Establecer un plazo de retención máximo basado en la finalidad del préstamo (ej. 5 años) y definir un mecanismo automático de eliminación o anonimización al vencimiento. Se debe acordar con el responsable (Biblioteca) la fecha límite y la metodología de eliminación.

Resultado: HTTP 200, cálculo correcto, citas verificadas y exportaciones base/TXT/CSV/HTML. 0 alertas de contenido conservadas.

### Caso 5: Divulgación a terceros

Entrada exacta: Caso ficticio TRA-001: se envía información académica de estudiantes de prueba a terceros por correo personal sin autorización y sin cifrado.

Identificador compartido por API/reporte/SQL: `5652bbce-295d-4f80-b708-a429b1cbb92d`.

Controles ISO relacionados y cotejados: A.3.7 (Pendiente de decisión); A.3.26 (Pendiente de decisión); A.1.2.3 (Incluido propuesto).

Primera medida propuesta: Implementar un proceso de autorización previa por escrito para cualquier transferencia de datos a terceros y exigir cifrado en tránsito para todos los canales de comunicación que involucren datos personales.

Resultado: HTTP 200, cálculo correcto, citas verificadas y exportaciones base/TXT/CSV/HTML. 1 alertas de contenido conservadas.


## 9. Verificación de referencias y límites semánticos

Se cotejaron las 9 referencias ISO y 11 legales de estos cinco casos contra sus
secciones/artículos PostgreSQL; las 14 relaciones RAG se contrastaron con sus
fragmentos recuperados. Los enlaces ISO por SHA respondieron y contenían las citas.
No se contaron coincidencias documentales como prueba de interpretación correcta.

Cuatro casos conservaron alertas de contenido. Persisten inferencias por confirmar,
por ejemplo atribuir carencias de trazabilidad o identidades a partir de evidencia
insuficiente. El informe las identifica como borradores; no aprueba ni implementa
las medidas. **No se ha demostrado una mejora global de calidad semántica del LLM.**

## 10. Reportes y presentación visual

PIMS-RIE-06 revisión 0.3 documenta el contrato de 26 campos. El generador implementa
una estructura propia en 11 secciones, no una copia de una plantilla recuperada.
Conserva anexo técnico, cálculo, opinión IA, fuentes y seguimiento separado.

TXT/base/CSV siguen disponibles. CSV conserva columnas anteriores y añade ID,
versión y trazabilidad. HTML aporta una mejora concreta: impresión A4, tablas,
jerarquía, encabezado académico, estado, referencias agrupadas y datos pendientes.
El PDF de prueba proviene de la impresión real del navegador, no de un nuevo motor
PDF del servidor. Ningún formato declara aprobaciones o reducción residual automática.

Chromium verificó formulario, resultados, referencias, historial, edición SQL de un
plan nuevo y restauración de sus campos. El reporte base permaneció idéntico. La
prueba del formulario reproduce la respuesta real guardada del caso 1 para no
repetir IA: **no es una sexta evaluación nueva del LLM**. Los cinco POST anteriores
sí fueron evaluaciones reales independientes.

Se probaron anchos 1440, 900 y 390. En 900/390 el ancho de documento fue exactamente
el de la ventana; HTML móvil también cumplió 390/390. No hubo errores JavaScript.
Se inspeccionaron las capturas y la primera página del PDF real; se mejoraron las
etiquetas legibles de estado. Las imágenes/PDF están en `datos/consolidacion/visual/`,
fuera de Git. No se inventaron capturas.

## 11. Pruebas automatizadas finales

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

Se ejecutaron 109 pruebas principales y 23 de historial/planes, con todas las
integraciones habilitadas y sin omisiones. Otra ejecución agrupada de 43 pruebas
SQL/documentales también pasó. La prueba antigua que requería B.3.9 real ahora
pasa con la ISO efectivamente incorporada. Los registros sintéticos SQL se revirtieron.

Cobertura nueva: corrección OCR sin alterar fuente, separación de secciones,
6.1.3/A/B en PostgreSQL, 78 filas SoA/roles, identidad de reporte, estructura,
pendientes explícitos, escape HTML, exportaciones y fuentes versionadas. La prueba
de formato no admitido cambió de HTML a ZIP porque HTML ahora es una salida válida.

## 12. Conservación, versiones y duplicados

Antes/después de importar, los hashes de `resultado` y `reporte_base` de las 23
evaluaciones anteriores resultaron idénticos. La auditoría final los verificó otra
vez, después de los cinco casos y pruebas de interfaz. No se recrearon tablas ni
bases, no se borraron registros históricos y no se reescribió `.env`.

La incorporación se limitó a ISO, PIMS-RIE-04 y PIMS-RIE-06; se repitió y conservó
conteos, claves y huellas. Hay 12 versiones archivadas. La copia de Ley 29733
sigue duplicada físicamente por su representación como artículos y como RAG; no
se la eliminó porque sostiene dos rutas existentes. Una consolidación futura debe
introducir alias y comprobar enlaces antes de retirar representaciones. El README
almacenado no coincide con el local, pero tiene cero fragmentos RAG y quedó intacto.

## 13. Comparación antes/después

| Caso | Entrada idéntica | Puntaje antes/después | ISO antes/después | Tiempo antes/después |
|---|---|---:|---:|---:|
| 1 | Sí | 12 / 12 | 0 / 1 | 39.39 / 77.88 s |
| 2 | Sí | 16 / 16 | 0 / 2 | 85.68 / 125.87 s |
| 3 | Sí | 15 / 15 | 0 / 1 | 96.53 / 130.06 s |
| 4 | Sí | 9 / 9 | 0 / 2 | 47.57 / 120.16 s |
| 5 | Sí | 20 / 20 | 0 / 3 | 89.11 / 154.69 s |

Las entradas son idénticas y los cálculos se conservaron. El corpus y el contexto
cambiaron: se agregó la ISO, se revisaron SoA/formato y aumentó el presupuesto de
contexto. Los tiempos son observaciones puntuales, **no un experimento causal**.
No se afirma mejora de latencia; varias respuestas nuevas tardan más. La presencia
de referencias ISO cotejadas pasó de cero a 9, lo que demuestra la capacidad nueva
de fundamentación, no la exactitud de todas las inferencias.

Para aislar el formato, ambos generadores procesaron el **mismo JSON congelado de
cada análisis nuevo**, sin otra llamada LLM ni cambio de fuentes:

| Campo medido con el mismo análisis congelado | Formato anterior | Formato nuevo |
|---|---:|---:|
| identificador | 0/5 | 5/5 |
| version formato | 0/5 | 5/5 |
| encabezado academico | 0/5 | 5/5 |
| resumen ejecutivo | 0/5 | 5/5 |
| objetivo alcance | 0/5 | 5/5 |
| conclusiones | 0/5 | 5/5 |

Estos son campos estructurales verificables, no una puntuación subjetiva de belleza.
La inspección visual nueva acredita legibilidad y ausencia de desbordamiento en
las condiciones probadas; no se capturó una comparación visual A/B anterior.

## 14. Errores encontrados y correcciones justificadas

- Secciones ISO ausentes y OCR B.14.4 omitido: extracción de cuerpo/tablas/guías,
  límites correctos y anotación de corrección, sin editar la norma privada.
- SoA de cinco controles: matriz de revisión de 78 con decisiones pendientes
  justificadas, sin forzar exclusiones o evidencias.
- Reporte sin UUID/versionado/estructura ejecutiva: formato propio alineado a RIE-06,
  identidad compartida con persistencia y vista de impresión.
- Categoría/huella ausentes en fragmentos institucionales: procedencia enriquecida
  desde PostgreSQL en lectura; no se reimportaron esas fuentes.
- Plan/reporte: se conservan responsables/plazos pendientes, controles propuestos y
  revisión humana; no se automatiza aceptación residual.
- En la inspección visual se detectaron etiquetas internas poco legibles y se
  presentaron estados en lenguaje natural. Las claves de API se conservaron.

## 15. Evidencias locales y protección de la norma

`datos/consolidacion/migracion.json`, `base_antes.json`, `auditoria_final.json`,
`suite-final.log`, `suite-experimento.log`, `funcional/caso_1..5.json`,
`funcional/caso_*_base/txt/csv.txt`, `funcional/caso_*_html.html` y
`visual/resultado.json`, imágenes y PDF. El material local sigue ignorado por Git.
Los documentos públicos del proyecto no reproducen íntegramente la norma; los
resúmenes de controles y decisiones de la SoA son redacción propia.

## 16. Limitaciones pendientes

Cotejo OCR con PDF autorizado; 67 decisiones SoA; confirmación de roles y datos de
alcance; bases jurídicas, destinatarios, plazos y evidencia operativa; aceptación
residual humana; revisión docente de las inferencias y de la presentación Word.
Las citas legales se cotejaron con el texto aportado, sin certificar actualización
jurídica o consolidación oficial. No hay evaluación de eficacia institucional.

## 17. Reproducción

Desde `agente_riesgos_pims_v3/`, con la configuración existente:

```bash
bash iniciar.sh --sin-navegador --port 8185
# Otra terminal; usar el puerto anunciado si está ocupado:
.venv/bin/python -m db.migrar --inventario
.venv/bin/python -m db.migrar --simular
# Solo si las fuentes locales fueron actualizadas:
.venv/bin/python -m db.migrar --solo ISO_IEC_27701_2025.md PIMS-RIE-04 PIMS-RIE-06
.venv/bin/python -m rag.indexar
.venv/bin/python validar_pims.py --url http://127.0.0.1:8185 --salida datos/consolidacion/funcional --repetir
PIMS_TEST_CONSOLIDACION=1 PIMS_TEST_DOCUMENTAL=1 PIMS_TEST_LECTURA=1 .venv/bin/python -m unittest discover -s tests -v
PIMS_TEST_EXPERIMENTO=1 .venv/bin/python -m unittest tests_experimento -v
```

La repetición crea evaluaciones nuevas y conserva las anteriores. La auditoría
`.venv/bin/python -m mantenimiento.verificar_consolidacion` usa solo lectura y respuestas
congeladas, y requiere las evidencias anteriores de comparación. Las utilidades
de autoría/visualización requieren `requirements-validacion.txt`; no son dependencias
obligatorias de la evaluación normal.

### Visor web local de PostgreSQL (23 de noviembre de 2026)

Se instaló pgAdmin en `agente_riesgos_pims_v3/datos/pgadmin/venv`, separado de
Flask, con estado privado y conexión al socket Unix existente de V3. No se
migraron documentos ni se modificaron las credenciales o tablas PostgreSQL.
El comando `.venv/bin/python visualizar_bd.py` inicia el visor en
`http://127.0.0.1:5050`, exclusivamente en la interfaz de bucle local.

La descarga inicial de pgAdmin 9.19 carecía de los archivos JavaScript
compilados y la interfaz quedó en «Loading». Se sustituyó por 9.10 después de
verificar que su paquete contiene `app.bundle.js` y `style.css`. Su estado de
configuración se guardó en una carpeta diferente para conservar el anterior.
`pip check` del entorno aislado devolvió `No broken requirements found`.

Chromium comprobó HTTP 200 en `/browser/`, carga sin errores JavaScript y
conexión real al servidor. Se desplegaron la base `pims_riesgos_experimental`,
el esquema `pims_riesgos` y sus tres tablas: `documentos`, `fragmentos` y
`versiones_documentales`. Se verificó el menú contextual `View/Edit Data`.
La captura privada `datos/pgadmin/tablas.png` conserva esa navegación.
Las posteriores automatizaciones para abrir la grilla encontraron límites
en los selectores y en la restauración del árbol del visor; no constituyen una
validación automatizada de la grilla de filas. El visor y su conexión sí
se comprobaron. `py_compile visualizar_bd.py` y `git diff --check` pasaron.
