# Agente PIMS V3

Única versión operativa. [Inicio rápido](../README.md) · [Operación de datos](../docs/OPERACION_V3.md).

## Funcionalidad

Evaluación de riesgos con matriz 1–5, justificación mediante Ollama, validación
de citas contra corpus PostgreSQL y seguimiento de tratamientos y actividades.
El reporte original se conserva; el ampliado incorpora responsables, plazos,
actividades y verificación. La edición concurrente se protege con versión y HTTP 409.
El estado verificado exige evidencia, verificador, fecha y actividades completas.

## Fuente documental en una instalación nueva

La preparación crea un corpus vacío con el esquema definitivo. Para cargarlo:

```bash
.venv/bin/python -m db.migrar
.venv/bin/python -m db.migrar --inventario
.venv/bin/python -m rag.indexar
```

`db.migrar` importa Ley-29733.md, documentos institucionales, metadatos y las
fuentes permitidas dentro del proyecto. La ISO privada debe colocarse en la raíz
como `ISO_IEC_27701_2025.md` (ignorada por Git). No se fabrican citas si falta.
Los PDF escaneados usan el caché OCR conservado en knowledge/.ocr_cache.
El indexado requiere Ollama y el modelo `embeddinggemma` instalado.
La conexión administrativa se usa solo en comandos de mantenimiento; las rutas
HTTP usan el rol limitado que puede leer el corpus y editar los planes.

### Expediente PIMS UNSA simulado

Los diez DOCX de `knowledge/documentos/pims_unsa/` se leen directamente,
incluidas sus tablas; no necesitan conversión ni nuevas dependencias. El cargador
extrae el código del contenido y comprueba su correspondencia con el archivo.
Registra título, versión, fecha, responsable propuesto, aprobación declarada,
referencias y relaciones TRA/ACT/RIE/ACC. Se importan como documentos del proyecto
académico, separados de las fuentes institucionales. Los TXT de instrucciones
del paquete quedan fuera del RAG.

```bash
.venv/bin/python -m db.migrar --simular  # extracción y metadatos, sin SQL
.venv/bin/python -m db.migrar
.venv/bin/python -m rag.indexar
.venv/bin/python -m db.migrar --inventario
.venv/bin/python -m rag.probar "TRA-002 bienestar permisos excesivos"
```

La identidad documental PIMS es su código: repetir la importación o renombrar
la fuente no duplica el registro. Dos archivos distintos con el mismo código
se rechazan antes de escribir. Las fuentes sustituidas se archivan con sus
fragmentos y originales; los vectores sin cambios se conservan y los modificados
requieren reindexación. Los reportes guardan el texto recuperado, versión,
SHA-256, localizador XML y puntajes de búsqueda. El enlace
`/api/fuente-rag/<sha256>/<fragmento>` permite cotejar fuentes vigentes y archivadas.
Un localizador de DOCX identifica párrafo/fila; no representa una página de Word.

El cálculo sigue siendo determinista: P × I, enteros 1–5; **1–5 Bajo,
6–11 Medio, 12–19 Alto, 20–25 Crítico**. PIMS-RIE-01, 02, 03A y 06 se
armonizaron con estas bandas en revisión 0.2; la fórmula no cambió. En escenarios Altos/Críticos Python fija prioridad alta; conserva la sugerencia
original del modelo por separado. La aceptación es humana. Los residuales de 03A son previstos, sin verificación ni aceptación.
La SoA 0.3 revisa los 78 controles: 11 inclusiones propuestas y 67 decisiones
pendientes (incluidos 18 casos de rol encargado). No acredita implementación ni
aprobación institucional. La ISO OCR se consulta desde PostgreSQL y requiere
cotejo con PDF en las referencias afectadas.

Con Flask iniciado mediante `bash iniciar.sh --sin-navegador`, ejecutar:

```bash
.venv/bin/python -m unittest discover -s tests -v
PIMS_TEST_DOCUMENTAL=1 PIMS_TEST_EXPERIMENTO=1 .venv/bin/python -m unittest tests.test_pims_documental tests_experimento -v
.venv/bin/python validar_pims.py --repetir
```

La última orden genera cinco evaluaciones **reales con datos ficticios** y las
guarda en el historial; conserva entradas, respuestas, tiempos, cotejos y
exportaciones en `datos/validacion_pims/` (privado, ignorado por Git).
`--repetir` vuelve a generar; `--caso 1` selecciona un caso. No compara calidad
generativa anterior: la comparación automática antes/después es del buscador
léxico con lector/selector de HEAD y corpus actual, sin cambiar la rama.
Consultar [la validación documental](../docs/VALIDACION_DOCUMENTAL_PIMS_27701.md)
para resultados y límites comprobados.

## Configuración

`preparar_demo.py` escribe `.env` con permisos privados y no lo sobrescribe.
Para instalaciones existentes, conservar el archivo y los datos. Las variables
OLLAMA_MODEL, OLLAMA_TIMEOUT y RAG_EMBED_MODEL permiten elegir los modelos locales.
La app solo acepta la base `pims_riesgos_experimental`; ese nombre histórico se
conserva deliberadamente. No se requiere ninguna otra aplicación del repositorio.

## Pruebas

Ver los comandos del README raíz. `pruebas_navegador.cjs` es una comprobación
opcional que necesita Playwright y una evaluación guardada; no elimina el historial.
La tabla de comparación contrasta el mismo análisis original con su plan vigente,
no compara dos servidores ni versiones de aplicación.


### Consolidación para la tercera entrega

PIMS-RIE-04 y PIMS-RIE-06 están en revisión 0.3. El formato dinámico propio es
PIMS-RIE-06 / 1.0, con UUID compartido con SQL, fecha estable, resumen, alcance,
cálculo, controles/SoA, tratamiento, residual, evidencias y conclusiones. TXT/base
conservan el análisis; CSV añade trazabilidad; **Vista de impresión** abre HTML
con tablas y estilos A4. El navegador permite imprimir o guardar PDF. Los reportes
históricos no se reescriben.

La ISO privada se guarda una vez, con 86 secciones específicas y 120 fragmentos
RAG: incluye 6.1.3, tablas A.1/A.2/A.3 y las 78 guías B. La corrección derivada
B.14.4 → B.1.4.4 se anota sin modificar el archivo original. Los códigos de las
tablas A y la enumeración de 6.1.3 siguen pendientes de cotejo. Los endpoints
`/api/fuente-iso/<codigo>?sha256=<huella>` consultan PostgreSQL y versiones archivadas.

Para actualizar **solo fuentes revisadas**, preservando el resto del corpus:

```bash
.venv/bin/python -m db.migrar --simular
.venv/bin/python -m db.migrar --solo ISO_IEC_27701_2025.md PIMS-RIE-04 PIMS-RIE-06
.venv/bin/python -m rag.indexar
```

La instancia de consolidación se comprobó en `http://127.0.0.1:8185`:

```bash
bash iniciar.sh --sin-navegador --port 8185
# Otra terminal; usa la dirección anunciada si el puerto está ocupado:
.venv/bin/python validar_pims.py --url http://127.0.0.1:8185 --salida datos/consolidacion/funcional --repetir
PIMS_TEST_CONSOLIDACION=1 PIMS_TEST_DOCUMENTAL=1 PIMS_TEST_LECTURA=1 .venv/bin/python -m unittest discover -s tests -v
PIMS_TEST_EXPERIMENTO=1 .venv/bin/python -m unittest tests_experimento -v
```

Las herramientas opcionales de autoría y pruebas visuales tienen dependencias
separadas. No son necesarias para ejecutar las evaluaciones normales:

```bash
.venv/bin/python -m pip install -r requirements-validacion.txt
.venv/bin/python -m mantenimiento.actualizar_soa
.venv/bin/python -m mantenimiento.actualizar_formato_informe
PLAYWRIGHT_BROWSERS_PATH=/tmp/pims-browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/pims-browsers .venv/bin/python pruebas_consolidacion_visual.py
```

La prueba visual reproduce una respuesta real guardada del caso 1 y comprueba
historial, edición/restauración de un plan nuevo e impresión. Los cinco POST del
validador sí generan IA nueva. Toda evidencia queda en `datos/`, fuera de Git.
Consulta [validación](../docs/VALIDACION_DOCUMENTAL_PIMS_27701.md) y
[justificación de mejoras](../docs/MEJORAS_IMPLEMENTACION_PIMS_27701.md).

### Visualizar PostgreSQL desde el navegador

El visor opcional pgAdmin se instala separado del entorno de Flask. Desde esta
carpeta, la instalación inicial es:

```bash
python3 -m venv datos/pgadmin/venv
datos/pgadmin/venv/bin/pip install pgadmin4==9.10
```

Para abrirlo después de la instalación:

```bash
.venv/bin/python visualizar_bd.py
```

Abre `http://127.0.0.1:5050`. Se configura en modo local, sin inicio de sesión
web, y escucha únicamente en este equipo. Usa la conexión existente de `.env`
y el usuario de aplicación, sin modificar credenciales ni ejecutar migraciones del
corpus. La configuración del visor queda en `datos/pgadmin/`, excluida de Git.
Su archivo SQLite guarda preferencias de pgAdmin; los documentos siguen en
PostgreSQL.

En el panel izquierdo abre **PIMS UNSA → PIMS V3 — PostgreSQL → Databases →
pims_riesgos_experimental → Schemas → pims_riesgos → Tables**. Sobre
`documentos`, usa **View/Edit Data → First 100 Rows** para ver el inventario.
`fragmentos` contiene los fragmentos RAG; `versiones_documentales`, el historial
documental. Las evaluaciones y planes están en el esquema
`gestitel_experimental`. Cierra el visor con `Ctrl+C` en su terminal.
