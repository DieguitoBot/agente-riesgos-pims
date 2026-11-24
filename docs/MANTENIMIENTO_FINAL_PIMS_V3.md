# Mantenimiento final PIMS V3 — 24/11/2026

## 1. Objetivo

Corregir incidencias comprobadas de higiene documental, acceso a fuentes y
validación automática, sin reconstruir V3. Medir el rendimiento y actualizar el
estado técnico sin reescribir evidencias históricas. Implementación académica
simulada, sin aprobación institucional ni certificación de cumplimiento.

## 2. Estado inicial y protección

La carpeta original estaba en `trabajo/expediente-privacidad-unsa`, HEAD `8f9dc59`,
con 36 archivos versionados modificados/eliminados y siete entradas sin seguimiento.
Incluía una reorganización local de scripts y documentación. No se sobrescribió,
guardó en stash ni confirmó ese trabajo; tampoco se cambió de rama en esa carpeta.

Se adaptó el procedimiento mediante un worktree separado:
`/tmp/pims-mantenimiento-final`, rama `mantenimiento/ajustes-finales-pims-v3`.
Se actualizaron las referencias remotas y se tomó `origin/main` en `53a886b`
(Merge PR #8, que incorpora `8f9dc59`). El `main` local no se movió. Los cambios
pendientes de la carpeta original no forman parte de este mantenimiento.

Antes de modificar el worktree: 109 pruebas descubiertas, 102 aprobadas y siete
omitidas por requerir integración real. No se inicializaron bases ni migraron fuentes;
se utilizó el entorno virtual existente solo como intérprete. La configuración se
cargó explícitamente desde el `.env` original en los procesos de integración, sin
copiarlo, enlazarlo ni modificarlo.

## 3. Incidencias confirmadas

| Incidencia | Evidencia en el main revisado | Corrección |
|---|---|---|
| Auxiliares en expediente | Dos TXT de operación junto a diez DOCX | Retirar ambos TXT del expediente versionado |
| Consulta documental sin control | Inventario, fuente RAG y fuente ISO accesibles sin comprobar cliente | Acceso local directo o token Bearer; sin caché |
| Rendimiento elevado | Medición real de 110,34 s, dominada por Ollama | Instrumentación optativa y limitación documentada |
| Estado Git desactualizado en informes | «Sin commits, push ni merge» sin delimitación histórica | Notas de estado posterior y enlace a este informe |
| Ausencia de CI | No existía `.github/workflows/` | Workflow mínimo y ejecución aislada de pruebas |

La ruta ISO también podía confundir indisponibilidad SQL con una fuente ausente:
`BaseNoDisponible` hereda de `OSError`. Ahora se trata primero y devuelve un 503
con mensaje genérico, sin exponer detalles de infraestructura.

## 4. Incidencias descartadas o no demostradas

- Los TXT ya estaban excluidos de la ingesta: no se confirmó contaminación del RAG
  por esos auxiliares. Se conserva la exclusión defensiva del lector.
- No faltaban los diez DOCX ni la revisión de los 78 controles. No fue necesario
  regenerarlos, cambiar sus versiones ni completar decisiones de aplicabilidad.
- No se identificó un cambio necesario en fórmula, bandas, contratos o formatos.
- No se demostró una optimización segura de inferencia mediante cambios pequeños.
  No se promete una reducción de tiempos ni se atribuyen diferencias al mantenimiento.
- No se comprobó una regresión visual que justificara rediseñar los reportes.

## 5. Archivos modificados

- `.github/workflows/pruebas-v3.yml`: integración continua.
- `README.md`, `agente_riesgos_pims_v3/README.md`, `.env.example` de V3:
  estado de incorporación, acceso documental y comandos nuevos.
- `docs/VALIDACION_DOCUMENTAL_PIMS_27701.md` y
  `docs/MEJORAS_IMPLEMENTACION_PIMS_27701.md`: aclaraciones históricas.
- Este informe.
- `app.py`, `seguridad_documental.py`: protección de tres consultas y error SQL ISO.
- `knowledge/documentos/pims_unsa/LEEME_PRIMERO.txt` y
  `PROMPT_CODEX_INTEGRACION.txt`: retirados. Ningún DOCX modificado.
- `mantenimiento/metricas.py` y `mantenimiento/medir_evaluacion.py`: captura optativa
  y evaluación de diagnóstico con salida reducida a tiempos y comprobaciones.
- `db/repositorio.py`, `rag/embeddings.py`, `rag/recuperar_contexto.py`,
  `knowledge/documento_iso.py`, `knowledge/documento_ley.py`,
  `knowledge/evidencia_rag.py`, `prompts/riesgo_prompt.py`, `llm/ollama_client.py`,
  `skills/evaluacion_riesgo.py`, `skills/reporte.py`, `experimento.py`:
  únicamente imports y decoradores de medición; no se altera su lógica.
- `tests/test_mantenimiento.py`: seguridad, contrato y captura de tiempos.
- `tests/run_unitarias.py`: descubrimiento de pruebas y bloqueo de SQL/HTTP reales.

Todas las rutas de aplicación de esta lista son relativas a `agente_riesgos_pims_v3/`.

## 6. Correcciones implementadas

El expediente contiene exclusivamente diez DOCX. Se conservan sus bytes, SHA-256,
identificadores, versiones y localizadores. No se modifica el corpus PostgreSQL ni
su historial documental para retirar los TXT: nunca se ingerían como evidencia.

El workflow usa Python 3.10, instala `requirements.txt` y `requirements-rag.txt`,
comprueba sintaxis y ejecuta el mismo runner verificado localmente. No necesita
PostgreSQL, Ollama, modelos, credenciales ni DOCX opcionales de terceros. Las pruebas
que requieren servicios reales quedan explícitamente deshabilitadas en ese runner.
Además bloquea las llamadas reales de psycopg y requests, incluso si existe `.env`.
Cualquier fallo de unittest o compilación produce salida no cero.

## 7. Justificación técnica y conservación de arquitectura

Se mantiene: documentación autorizada → importación → PostgreSQL → recuperación
RAG → evaluación determinista → Ollama → validación de referencias → reportes.
No se crea almacenamiento documental alternativo, caché de normativa ni JSON de
fuentes. La captura de tiempos usa ContextVar, aislada por contexto de ejecución.
Sin captura explícita no se cronometra; no se agregan campos a la respuesta pública
ni al resultado persistido. También contabiliza etapas fallidas y reintentos.

Se conserva P × I, enteros de 1 a 5, y las bandas 1–5 Bajo, 6–11 Medio,
12–19 Alto y 20–25 Crítico. La prueba existente recorre las 25 combinaciones.
La metodología continúa vinculada a PIMS-RIE-01 revisión 0.2.

## 8. Medidas de seguridad

Las tres rutas documentales mantienen sus URL y contenido para clientes autorizados:

- Conexión loopback directa, Host local y sin origen distinto ni cabeceras de proxy:
  acceso sin token con `PIMS_DOCUMENTOS_LOCAL=1` (predeterminado).
- Otros clientes: requieren `Authorization: Bearer ...` coincidente con
  `PIMS_DOCUMENTOS_TOKEN`, mediante comparación constante. Sin secreto configurado,
  el acceso remoto a estas rutas queda denegado con 401 antes de consultar SQL.
- No se aceptan credenciales por query string. No se registran tokens, prompts
  ni normativa en las métricas. Respuestas con `no-store, private`, `nosniff` y
  `no-referrer`, incluidos los errores controlados.
- No se utiliza `X-Forwarded-For` para conceder acceso. Detrás de un proxy se debe
  usar `PIMS_DOCUMENTOS_LOCAL=0`, incluyendo proxies que oculten sus cabeceras.
- Los mensajes de indisponibilidad documental no incluyen DSN, rutas ni excepciones.

Esto no constituye autenticación global de toda la aplicación. Evaluaciones e
historial contienen extractos y conservan su contrato. El lanzador sigue ligado a
127.0.0.1. Publicar el agente en red exige un control global de acceso en el despliegue;
el token documental debe viajar por HTTPS o un túnel de confianza. Los enlaces de
cotejo locales no cambian ni llevan secretos. La normativa privada sigue fuera de Git.

## 9. Rendimiento medido

Una evaluación real del caso ficticio TRA-001 / ACT-001 / RIE-001, modelo configurado
`qwen3.5:4b-q4_K_M`, una llamada a Ollama, búsqueda semántica habilitada, corpus
local de 29 documentos y 2.302 fragmentos RAG. Se cargó la configuración existente;
no se cambiaron modelo, límites de contexto, fuentes ni parámetros de generación.
Se utilizó Flask test_client para el POST real, con SQL y Ollama reales.

| Etapa | Segundos | Observación |
|---|---:|---|
| Respuesta API, incluida persistencia | 110,341430 | JSON y enrutamiento Flask incluidos; sin red HTTP externa |
| Evaluación | 110,304040 | Incluye recuperación, IA, validación y reporte |
| PostgreSQL: normas | 0,012173 | Dos lecturas, incluidas conexión y decodificación |
| Construcción/selección ISO | 0,007556 | Incluye su lectura SQL |
| Construcción/selección legal | 0,004835 | Incluye su lectura SQL |
| PostgreSQL: fragmentos | 0,444303 | Una lectura |
| PostgreSQL: vectores | 0,762378 | Una lectura |
| Embedding de consulta | 5,769199 | Una llamada real a Ollama para embedding |
| Selección RAG | 0,386300 | BM25, filtrado y selección |
| RAG completo | 7,541834 | Incluye SQL, embedding, similitudes y selección |
| PostgreSQL: SoA | 0,005567 | Una lectura |
| Construcción de mensajes | 0,000482 | Sin reducir contexto |
| HTTP Ollama /api/chat | 102,738101 | Incluye espera, carga, inferencia y transporte local |
| Cliente Ollama completo | 102,740570 | Incluye validación y JSON |
| Validación de vínculos | 0,000153 | Una pasada |
| Validación complementaria | 0,000304 | Referencias ISO e indicadores |
| Validación legal | 0,000042 | Referencias legales |
| Validación RAG | 0,000089 | Citas y procedencia |
| Reporte TXT | 0,000222 | Generador existente |
| Persistencia | 0,035202 | Identificador conservado en historial |

Las etapas padre e hijas se solapan: no se deben sumar todas las filas.
El tiempo de Ollama representa aproximadamente el 93,1 % del total. No se aisló
el tiempo puro de GPU/CPU ni la carga de modelo del tiempo HTTP; no se atribuye
esa duración exclusivamente a generación de tokens. Tampoco se controlaron temperatura
del hardware, carga concurrente o calentamiento de modelos.

No se aplicaron optimizaciones especulativas. Se deja instrumentación reproducible
para posteriores mediciones. Esta ejecución no es una comparación antes/después con
los 77,88–154,69 s históricos: las condiciones y el corpus no son idénticos.

Resultado: HTTP 200, IA válida, puntaje 12 / Alto, 12 fuentes recuperadas,
2 referencias ISO, 2 legales y 3 RAG verificadas. Identificador persistido:
`eaaed2c3-7f27-48fa-ab95-75063376c654`.

## 10. Pruebas ejecutadas

- Suite inicial en main actualizado: 109 descubiertas, 102 aprobadas, siete omitidas.
- Suite final determinista: 140 descubiertas, 127 aprobadas y 13 de integración
  omitidas; incluye las pruebas anteriores y ocho nuevas de mantenimiento.
- Integración real: 13 pruebas aprobadas en 3,590 s. Lectura de esquemas actual e
  histórico, diez DOCX indexados y cotejables, migración idempotente/versiones con
  rollback, ISO con 86 secciones, SoA de 78, persistencia, edición con control de
  versión, permisos del rol y CSV con neutralización de fórmulas.
- Flask servido temporalmente en loopback: GET `/`, `/api/status`, `/api/documentos`,
  historial, fuente RAG y fuente ISO con/sin SHA-256: todos HTTP 200. Se cerró solo
  el servidor creado para esta comprobación.
- Sintaxis Python mediante `compileall`, sintaxis de ambos JavaScript mediante
  `node --check` y `git diff --check`: sin errores. La inspección adicional de
  archivos nuevos tampoco encontró espacios finales.
- Comparación SHA-256: los diez DOCX son idénticos a `main`; los 116 archivos
  previos inventariados en la carpeta original conservan sus bytes. ISO privada
  y `.env` siguen ignorados; no se detectaron patrones de credenciales en los cambios.
- Evaluación real descrita arriba: TXT HTTP 200 (37.615 bytes), base HTTP 200
  (32.806 bytes), CSV HTTP 200 (5.124 bytes), HTML HTTP 200 (28.452 bytes).
- Pruebas existentes confirman escape HTML, botón de impresión/guardado PDF,
  compatibilidad con resultado histórico, UUID y fecha estable, cálculo Python,
  residuales pendientes y advertencias de simulación. No se generó un PDF real ni
  se ejecutó un navegador en esta fase.

Las pruebas SQL usan transacciones de ensayo revertidas. La evaluación real autorizada
sí añade un registro al historial. No se borraron evaluaciones ni se reescribieron
reportes históricos. Los valores reales anteriores son evidencias de esta sesión;
los informes históricos mantienen sus propias cifras.

Para reproducir las unitarias: `python tests/run_unitarias.py` desde V3.
Las integraciones se habilitan con `PIMS_TEST_LECTURA=1`,
`PIMS_TEST_DOCUMENTAL=1`, `PIMS_TEST_CONSOLIDACION=1` y
`PIMS_TEST_EXPERIMENTO=1`, sobre una base local ya preparada. No usar el runner
unitario para integraciones: desactiva intencionalmente esos flags y las conexiones.

## 11. Compatibilidad con el orquestador

Se consultó en modo lectura el orquestador, revisión
`434f5abaae0e2f8bead538e6695dcac350877487`:
[app/adapters.py](https://github.com/DieguitoBot/pims-orquestador/blob/434f5abaae0e2f8bead538e6695dcac350877487/app/adapters.py).
El adaptador de riesgos hace POST a `/api/evaluar`, envía la entrada JSON y
puede añadir Authorization Bearer. No llama a los tres endpoints documentales
protegidos. No se modificó ningún archivo de ese repositorio ni de los otros agentes.

La nueva regresión hace una evaluación con cliente remoto, sin token documental,
y verifica entrada, campos de salida, códigos HTTP, cálculo, UUID y llamada de
persistencia. `/api/status` conserva acceso y contrato. Las pruebas existentes
siguen cubriendo 400 por entrada inválida, 503 al exigir IA no disponible o fallar
persistencia, además de planes e historial. No se ejecutó el sistema completo de
ocho agentes; la compatibilidad se acredita mediante lectura del adaptador y
regresiones locales, no mediante una ejecución distribuida.

## 12. Limitaciones pendientes

La inferencia local domina la latencia. Harían falta mediciones repetidas bajo
condiciones controladas antes de proponer cambios de hardware o configuración.
No se cambió el modelo ni se redujeron fuentes para mejorar tiempos.

El control documental no sustituye la autorización global para un despliegue
público. Un proxy requiere configuración explícita. La interfaz remota con token
y la ejecución distribuida de los ocho agentes no se probaron en un despliegue real.

El workflow se verificó localmente mediante sus comandos; no se ha ejecutado en
GitHub Actions porque no se hizo push ni PR. Tampoco se produjo un PDF nuevo.
Persisten los cotejos OCR, decisiones SoA y aprobación humana descritos en los
informes históricos: 11 propuestas y 67 decisiones pendientes, sin inventar
implementación o aceptación residual.

## 13. Recomendaciones finales

Revisar el diff del worktree de mantenimiento y coordinar su integración con la
reorganización pendiente en la carpeta original antes de publicar. Conservar el
worktree hasta guardar o incorporar sus cambios: `/tmp` es almacenamiento temporal.
Mantener `.env`, clúster, normativa y evidencias privadas fuera de Git.
Ejecutar posteriormente CI en GitHub y una comprobación visual/PDF si se requiere
una evidencia de presentación. No se realizaron push, PR, merge ni commits de
esta nueva fase. Los cambios quedan disponibles para revisión local.
