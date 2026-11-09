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
