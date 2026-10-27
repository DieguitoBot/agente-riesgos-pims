# Calidad de reportes y recuperación documental

Registro histórico del 26 de octubre de 2026, rama `mejora/calidad-reportes-rag`.
Continúa la integración de interfaz y documentos de `origin/main` (`9f550cc`).

## Estado actualizado — 27 de octubre de 2026

- Modelo principal: `qwen3.5:4b-q4_K_M`. Se conserva `embeddinggemma` para
  recuperación documental; `qwen2.5:3b` fue eliminado y se verificó la lista local.
- Documento ISO disponible localmente y excluido de Git. El escenario de prueba
  recupera seis fragmentos ISO y dos artículos legales por búsqueda temática.
- Sin cupos de riesgos, indicadores o referencias. Contexto predeterminado de
  32.768 tokens y presupuesto de salida de 16.384; respuestas truncadas rechazadas.
- 79 pruebas automatizadas aprobadas. Se incluye vinculación de cada fuente
  con sus propios extractos en el contrato, además del cotejo posterior.
- La primera prueba retomada falló tras dos intentos en 1.253,9 segundos por
  una referencia RAG inválida. No se publicó el análisis como reporte de IA.
- Con el esquema corregido, la prueba terminó al primer intento en **629,5 segundos**:
  5 citas ISO, 1 legal y 5 RAG cotejadas. La revisión encontró supuestos sin sustento,
  relaciones RAG genéricas e indicadores inadecuados; no se aprobó el contenido.
- Se añadieron alertas parciales de coherencia y un encabezado de borrador. Se comprobó
  su comportamiento con regresiones y con el contenido de la salida real guardada.
- Se entregó `../agente_riesgos_pims_v2/reporte_ejemplo_revisado.md`, corregido por el
  asistente y diferenciado de la salida automática. Incluye 3 riesgos sustentados,
  5 indicadores y datos pendientes, sin inferir controles ausentes del silencio.
- Validación retomada terminada; no quedan generaciones en curso. Qwen 3.5 no quedó
  acreditado como generador autónomo de reportes correctos y sigue siendo lento en CPU.
  Detalle en `../ESTADO_VALIDACION.md`.

Las secciones siguientes documentan los ensayos anteriores; las cifras y
pendientes del 26 de octubre no describen la configuración actual.

## Cambios históricos

- Segmentación por palabras/oraciones con solapamiento, preservación de secciones
  Markdown y exclusión de fragmentos muy breves. El corpus local genera 430
  fragmentos frente a los 555 de la primera integración.
- Prefijos de documento/consulta para EmbeddingGemma e índice versión 2.
  Recuperación híbrida con similitud semántica, términos BM25, eliminación de
  resultados casi duplicados y un máximo de dos fragmentos por archivo.
- Prompt orientado a riesgos distintos, medidas sobre los activos descritos,
  criterios de cierre, controles existentes y datos por confirmar.
- Contrato por solicitud que limita evidencias a frases literales disponibles
  (8–500 caracteres) y referencias a IDs/artículos/controles recuperados. Si no
  hay frases apropiadas, se conserva el cotejo literal posterior.
- Validación de evidencia literal de cada riesgo antes de aceptar el análisis;
  el reintento conserva los documentos y explica el error.
- Relaciones RAG con ID de fuente, cita cotejada, hecho del escenario y aplicación
  propuesta. Las referencias descartadas tampoco aparecen en `analisis_ia`.
- Reporte e interfaz distinguen citas utilizadas de fuentes recuperadas e incluyen
  los extractos. Se rechazan títulos legales usados como cita e indicadores con
  aritmética de constantes o fuentes de medición vacías de contenido.
- Pruebas ISO con un documento sintético temporal. La aplicación sigue informando
  la ausencia del Markdown autorizado; los tests no sustituyen esa fuente real.

## Validación automatizada

Desde `agente_riesgos_pims_v2/`:

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/js/app.js
```

69 pruebas aprobadas con las dependencias RAG instaladas. Sintaxis JavaScript y
`git diff --check` aprobados. Se cubren API, exportación, contrato de interfaz,
citas falsas, hechos inventados, reintento, recuperación y compatibilidad de índice.
Las respuestas de IA en estas pruebas son simuladas.

## Repetir la comprobación real

Con Ollama iniciado y ambos modelos instalados:

```bash
.venv/bin/python -m rag.indexar
.venv/bin/python comprobar_ia.py --entrada ejemplo_calidad_rag.json
```

El caso es ficticio: hoja de cálculo con enlace público, cuenta compartida,
respaldo diario restringido y conservación indefinida. Permite revisar si el
modelo distingue exposición, trazabilidad y conservación, sin inventar una
filtración ni afirmar que no existen respaldos.

## Diagnóstico de rendimiento y modelo

Ollama 0.35.0 ejecuta la inferencia en CPU (Ryzen 7 5800H; 15 GiB de RAM
reportados). La GPU integrada no estaba activa para inferencia. El modelo
`qwen2.5:3b` falló las dos respuestas del primer ensayo real en 397,8 segundos.
En otro ensayo, con diagnóstico explícito de la evidencia errónea, también falló
tras 367 segundos: usó un archivo y supuestas páginas como evidencia del caso.
La validación impidió publicar ambos análisis como reportes de IA.

Se añadió separación de hechos citables y documentos; el prompt ya no expone
ordinales de fragmento ni puntuaciones de búsqueda que puedan confundirse con
páginas o certezas. Para Qwen 3/3.5 se usa `think: false`, temperatura 0,2,
penalización de presencia 0 y hasta 3.600 tokens de salida. Los otros modelos
conservan su solicitud compatible. Fuentes de configuración:
[Ollama: thinking](https://docs.ollama.com/capabilities/thinking) y
[Qwen 3.5 4B Q4_K_M](https://ollama.com/library/qwen3.5:4b-q4_K_M).

## Estado histórico al publicar el avance del 26 de octubre

- El código y las pruebas de recuperación, citas, reporte y contrato están listos.
- Con la separación mejorada de hechos y fuentes, `qwen2.5:3b` produjo un análisis
  estructuralmente válido al primer intento en **217,3 segundos**. La revisión
  encontró recomendaciones genéricas y **cero citas RAG verificadas**. Este ensayo
  aún no usaba el contrato restringido por solicitud añadido posteriormente.
- Se inició la descarga de `qwen3.5:4b-q4_K_M` (3,3 GB). **No se ha completado
  su evaluación ni cambiado el modelo predeterminado** en esta entrega.
- La evaluación real con el contrato final, la comparación con Qwen 3.5 y la
  selección del modelo definitivo siguen pendientes. Las 69 pruebas automáticas
  usan respuestas simuladas y no acreditan la calidad semántica del modelo nuevo.

Para continuar, desde `agente_riesgos_pims_v2/`, con Ollama iniciado:

```bash
# Este comando reanuda la descarga si sigue incompleta.
ollama pull qwen3.5:4b-q4_K_M
.venv/bin/python comprobar_ia.py --modelo qwen3.5:4b-q4_K_M --entrada ejemplo_calidad_rag.json
```

Revisar antes de cambiar `config.py`: riesgos distintos; reconocimiento del
respaldo existente; revocación del enlace público; cuentas individuales;
conservación vinculada a finalidad; citas RAG realmente cotejadas; duración.
El resultado de ese ensayo debe añadirse aquí. No afirmar todavía que el nuevo
modelo es más rápido o que resolvió la calidad del informe.

## Límites

Una cita cotejada demuestra procedencia textual, no corrección de la interpretación.
La relevancia de una búsqueda no es una probabilidad de acierto. Un plan de otra
organización sirve de referencia y no impone obligaciones a la universidad.
La suite sintética no valida el contenido de la norma ISO ni la precisión general
del modelo. El documento ISO faltaba durante los ensayos del 26 de octubre; ya está disponible localmente.
La revisión visual en navegador y una evaluación amplia con varios escenarios
no forman parte de los resultados automatizados registrados aquí.
