# Agente de evaluación de riesgos de privacidad · v2

Python + Flask + HTML/CSS/JavaScript. Esta versión trabaja de manera independiente:
identifica riesgos, compara valoraciones y propone medidas; no se conecta con otros
agentes ni realiza auditorías o decisiones legales.

Para instalar desde cero, consulta la [guía del repositorio](../README.md).

## Iniciar

```bash
cd agente_riesgos_pims_v2
.venv/bin/python -m db.local iniciar
bash iniciar.sh
```

El lanzador reutiliza el entorno existente, elige un puerto libre entre 8080 y 8100
y abre el navegador. Para aplicar cambios, detén solo la terminal de la v2 con
Ctrl+C, vuelve a iniciar y recarga la página. También admite `--sin-navegador` y
`--port 8080`. No detiene otras aplicaciones.

Ollama debe estar funcionando con un modelo local instalado. Comprueba en tu
terminal `ollama list`; si el servicio no está iniciado, usa `ollama serve`.
La pantalla comprueba el servicio y permite elegir cualquiera de los modelos
instalados. La elección se aplica a esa solicitud, sin cambiar variables globales.
No se descargan modelos automáticamente.

| Variable | Predeterminado |
| --- | --- |
| OLLAMA_URL | http://127.0.0.1:11434 |
| OLLAMA_MODEL | qwen3.5:4b-q4_K_M |
| OLLAMA_TIMEOUT | 900 segundos por solicitud de generación |

Se carga `.env` sin sobrescribir las variables de la terminal. Allí se configuran
`PIMS_DATABASE_URL` (lector) y `PIMS_DATABASE_ADMIN_URL` (administración).
La instancia privada ya está configurada en este equipo. Ejemplo con otro modelo:

```bash
OLLAMA_MODEL='nombre:etiqueta' ./iniciar.sh
```

## Reporte de IA

El modelo genera un análisis JSON: hechos, vulnerabilidades, amenazas, daños a las
personas, medidas, prioridad, verificación, valoración propia y referencias.
Python valida su estructura, calcula puntajes y comprueba las citas normativas;
construye el reporte descargable a partir de ese análisis, sin otra llamada al LLM.
La pantalla permite descargar el texto completo. La descarga conserva el escenario
evaluado aunque después cambies el formulario.

La interfaz exige una respuesta de IA válida. Un timeout, modelo ausente o respuesta
inválida muestra el motivo y permite elegir otro modelo o reintentar. No ofrece un
reporte básico como si fuera IA. La API conserva el respaldo de reglas para sus
consumidores anteriores, con un origen explícito.

Se solicitan todos los riesgos sustentados, indicadores por riesgo y referencias pertinentes,
sin cupos numéricos en el contrato. Cada riesgo distingue hechos, inferencias, amenaza,
vulnerabilidad, daño, medida, prioridad y criterio de cierre. No se añaden riesgos sin evidencia.
Se recuperan todos los controles ISO y artículos legales con coincidencias temáticas
(fragmentos de 2.200 y 1.800 caracteres respectivamente) y hasta 12 fragmentos RAG,
con un máximo de 2 por archivo para mantener diversidad. La recuperación sigue siendo
selectiva: un reporte extenso no garantiza cobertura documental exhaustiva.

Ollama recibe el contrato JSON mediante `format`. `OLLAMA_NUM_CTX` configura el contexto
(predeterminado: 16384 tokens) y `OLLAMA_NUM_PREDICT` el presupuesto de salida
(predeterminado: 5120); ambos deben ser positivos y la salida menor que el contexto.
Son límites técnicos configurables, no cuotas de riesgos. Una respuesta truncada se rechaza.
Para Qwen 3/3.5 se usa `think: false`, temperatura 0,2 y penalización de presencia 0,
con el mismo presupuesto completo de salida. El modelo principal es `qwen3.5:4b-q4_K_M`;
`embeddinggemma` sigue siendo necesario para el RAG. No se necesita mantener Qwen 2.5.
El contrato vincula cada fuente con sus propios extractos literales mediante alternativas JSON Schema;
la validación vuelve a comprobar la correspondencia entre cita y fuente, riesgo y evidencia.
Ante formato, citas o evidencia inválidos se permite un reintento detallado que conserva las fuentes.
No se acepta un informe breve como sustituto. No se repiten errores de conexión ni timeouts.
`OLLAMA_TIMEOUT` vale 900 segundos por defecto; dos intentos pueden consumir el doble.
Un contexto mayor requiere más memoria y tiempo; no equivale a mayor precisión garantizada.
La interfaz muestra tiempo transcurrido y espera la respuesta sin streaming.

El RAG combina similitud de embeddings almacenados en PostgreSQL y términos BM25,
filtra fragmentos breves y diversifica fuentes. Usa el modelo `embeddinggemma`;
`python -m rag.indexar` genera solo los vectores ausentes o de otro modelo.
No hay que ejecutarlo para cada evaluación. `PIMS_BUSQUEDA_SEMANTICA=0` permite
búsqueda por términos; también se conserva esta búsqueda si falla el servicio de
embeddings. FAISS y `requirements-rag.txt` sirven para importar fuentes y usar
herramientas históricas, no para consultar el corpus PostgreSQL ya cargado.
El reporte y la interfaz muestran las citas
RAG cotejadas, su aplicación propuesta, archivo, página y extractos recuperados.

## Conocimiento documental y controles específicos

La aplicación lee PostgreSQL. Los originales utilizados en la importación son:

- `../ISO_IEC_27701_2025.md`: Markdown OCR. Recuperación temática del anexo B sobre
  un catálogo parcial de 13 controles del anexo A, filtrado por rol.
- `../Ley-29733.md`: recuperación temática de artículos para explicar riesgos de
  privacidad. No constituye una versión oficial consolidada verificada.

Cada referencia se vincula a un riesgo y a un hecho literal del escenario. Las
citas se cotejan con el fragmento que recibió el modelo. Se descartan códigos,
artículos, citas o hechos inventados en las referencias. El reporte incluye fuentes,
líneas, páginas OCR para ISO y SHA256 de ambos documentos. Una cita válida acredita
procedencia textual; la interpretación requiere revisión humana.

El reporte identifica el control específico, por ejemplo A.3.9 (Permisos de acceso),
su guía B.3.9, la posible brecha y la evidencia necesaria para comprobarla. El anexo A
contiene controles; el B guía su implementación. No se declara un anexo completo
"vulnerado" ni una no conformidad confirmada basándose solo en el relato.

El documento legal incluye concordancias históricas al reglamento de 2013; estas
se excluyen de los fragmentos recuperados. El reglamento aprobado por D.S.
016-2024-JUS entró en vigor el 31 de marzo de 2025, según la
[Autoridad Nacional de Protección de Datos Personales](https://www.gob.pe/institucion/anpd/campa%C3%B1as/128319-nuevo-reglamento-de-proteccion-de-datos-personales).
Su texto no está incorporado a esta versión: no se inventan artículos del nuevo
reglamento ni se certifica actualidad de todo el Markdown del usuario.

La selección temática y el catálogo son parciales; una lista vacía no demuestra
cumplimiento. El RAG semántico complementa esta selección temática; no la convierte en exhaustiva.
Fuente del catálogo de códigos/temas:
[BSI, revisión 2025, páginas 24–32](https://www.bsigroup.com/siteassets/pdf/th-th/products-and-services/th-as-cross-lg-ict-dt-iso27701-mp-iso27701revisionwebinar-1125.pdf).
Los temas españoles son resúmenes propios.

## API

`POST /api/evaluar`:

```json
{
  "descripcion": "La universidad almacena DNI sin control de acceso y sin plazo de conservación.",
  "probabilidad": 3,
  "impacto": 4,
  "categorias": ["Identificación"],
  "rol_privacidad": "responsable",
  "modelo": "qwen3.5:4b-q4_K_M",
  "exigir_ia": true
}
```

`modelo` es opcional; usa la configuración del servidor si se omite o es null.
`rol_privacidad` admite responsable, encargado, ambos o no_definido. Las entradas
inválidas devuelven 400 antes de generar texto.

La respuesta conserva los campos anteriores y añade:

- `referencias_ley`: relaciones con artículos y citas verificadas.
- `documentacion_ley`: estado, artículos recuperados y huella documental.
- `referencias_rag`: citas cotejadas y su relación propuesta con cada riesgo.
- `fuentes_rag`: fragmentos recuperados con ID, archivo, página y texto.
- `estado_rag`: disponibilidad de PostgreSQL y resultado de recuperación.
- `reporte_texto`: reporte completo listo para exportar.
- `reporte_ia_generado`: true únicamente cuando el análisis proviene del modelo.

`exigir_ia: true` devuelve 503 y `codigo: "ia_no_disponible"` ante un fallo del LLM,
con `resultado_preliminar` identificado como reglas. Sin ese parámetro se conserva
HTTP 200 y `modo: "reglas_locales"`. El respaldo no tiene valoración IA ni referencias
normativas generadas. `GET /api/status` lista modelos; `/api/fuente-iso/<codigo>` y
`/api/fuente-ley/<numero>` muestran las secciones utilizadas como texto plano.

Matriz académica: probabilidad × impacto, ambos 1–5; 1–5 Bajo, 6–11 Medio,
12–19 Alto, 20–25 Crítico. Python conserva la valoración del usuario y calcula
separadamente la opinión IA. La matriz no es una escala prescrita por ISO.

## Visualizar la base de datos

Desde esta carpeta ejecuta `bash abrir_pgadmin.sh` y abre
<http://127.0.0.1:5050>. En el servidor **PIMS - Riesgos (local)** despliega
**Databases → pims_riesgos → Schemas → pims_riesgos → Tables**.
Clic derecho → **View/Edit Data → All Rows** sobre `documentos`, `fragmentos`
o `controles_iso`. La API `GET /api/documentos` muestra el inventario.

La lectura admite el esquema histórico JSON y el esquema actual con columnas
separadas para texto, página, línea y sección. Las columnas tienen prioridad.
`db.migrar` conserva el formato de escritura histórico: no usar para reimportar
sobre la base normalizada actual ni sobre ediciones realizadas en pgAdmin.

Consulta [la guía de demostración](../docs/GUIA_DEMOSTRACION.md) para probar el
escenario y explicar el recorrido de los datos.

## Comprobar y generar desde la terminal

```bash
# Desde agente_riesgos_pims_v2/, con el entorno instalado:
.venv/bin/python comprobar_ia.py
```

Este comando analiza `ejemplo_solicitud.json` con Ollama real, mide la duración y
guarda `reporte_ia.txt` únicamente si hay análisis IA válido. Admite `--modelo`,
`--entrada archivo.json` y `--salida reporte.txt`. Sale con código 1 si falla; no
reemplaza la salida con reglas ni elimina un reporte anterior.

Verificación automatizada:

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/js/app.js
```

Las pruebas ISO utilizan un documento sintético temporal, sin reproducir ni
requerir el documento privado. Para emitir referencias ISO, la base debe contener
una copia autorizada real; los datos sintéticos no se cargan fuera de los tests.
`PIMS_TEST_LECTURA=1 .venv/bin/python -m unittest tests.test_postgres_lectura -v`
comprueba ambos formatos mediante SQL y consulta el corpus sin modificarlo.

Consulta [la validación de esta entrega](../docs/CALIDAD_REPORTES_RAG.md).
Para repetir la evaluación real con un escenario ficticio:

```bash
.venv/bin/python comprobar_ia.py --entrada ejemplo_calidad_rag.json
```

El comando muestra cuándo empieza cada intento y el motivo de un eventual rechazo.
Solo guarda el reporte cuando la respuesta supera la validación automática; todavía
requiere revisión del contenido, de las inferencias y de la aplicabilidad de las fuentes.
La respuesta incluye `estado_revision` y `alertas_contenido`: se advierten algunas
carencias inferidas de información desconocida, hechos diferentes entre riesgo e
indicador y aplicaciones RAG repetidas. Son alertas parciales; su ausencia no acredita
corrección. La exportación identifica el texto como borrador y muestra estas alertas
al inicio. El ensayo real y sus límites están en [la guía de demostración](../docs/GUIA_DEMOSTRACION.md).
