# Integración local de interfaz y RAG — 26 de octubre de 2026

Registro histórico de la primera integración. Los ajustes y resultados posteriores
están en [Calidad de reportes RAG](CALIDAD_REPORTES_RAG.md).

Rama de prueba: `integracion/interfaz-tratamiento-rag`.

Se guardó la interfaz en el commit `469add0` y se integró `origin/main`
hasta `9f550cc` mediante el merge `e48384f`, sin conflictos.
La rama local `main` y el repositorio remoto no se modificaron.

La integración conserva las pestañas de evaluación, resultados y tratamiento,
la tabla de propuestas y el estado/fuentes del RAG. Los cinco documentos nuevos
aportan 555 fragmentos extraíbles. El índice se genera en cada equipo y está
excluido de Git.

## Ejecutar en este equipo

Desde la raíz del repositorio:

```bash
cd agente_riesgos_pims_v2
bash iniciar.sh
```

Detener primero la instancia anterior con Ctrl+C y abrir la dirección impresa
por el lanzador. Si hay otra instancia activa, el lanzador elegirá otro puerto.
Recargar la página después de reiniciar.

## Preparar otro equipo

Desde `agente_riesgos_pims_v2/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-rag.txt
ollama pull qwen2.5:3b
ollama pull embeddinggemma
.venv/bin/python -m rag.indexar
.venv/bin/python -m rag.probar "Una universidad publica DNI sin control de acceso"
bash iniciar.sh
```

Ollama debe estar funcionando; si no hay un servicio activo, ejecutar
`ollama serve` en otra terminal. Reindexar cuando cambien los documentos o
el modelo de embeddings.

## Alcance de la validación

- Fusión sin conflictos; cambios locales de interfaz conservados.
- JavaScript: comprobación de sintaxis aprobada.
- Suite existente con regresiones de interfaz: 48 de 54 pruebas aprobadas.
  Los seis fallos corresponden al documento local ausente
  `ISO_IEC_27701_2025.md`; los PDF del RAG no sustituyen ese lector Markdown.
- Los cinco documentos se extraen correctamente.
- FAISS: almacenamiento, recarga y búsqueda comprobados con vectores sintéticos.

La recuperación documental no demuestra por sí sola que cada referencia sea
aplicable. La propuesta de controles tampoco demuestra una reducción del riesgo.
La interfaz conserva el riesgo residual pendiente de reevaluación.

## Prueba real del RAG en este equipo

Se instalaron las dependencias opcionales y el modelo `embeddinggemma`.
Se generó un índice local de **555 fragmentos y 768 dimensiones**.

Dos consultas reales finalizaron con estado `recuperado`:

- «protección de datos personales consentimiento del titular y seguridad de la
  información»: recuperó textos pertinentes de `ley_29733.md`, además de una
  portada del plan de tratamiento.
- «Una universidad publica DNI sin control de acceso»: devolvió fragmentos del
  estatuto demasiado breves y poco pertinentes (páginas 16, 113, 36 y 119).

Hay 14 fragmentos de menos de 100 caracteres. Antes de aceptar la calidad del
RAG conviene revisar la segmentación (evitar colas aisladas y portadas) y evaluar
un conjunto de consultas representativas. Esta integración no modifica todavía
el algoritmo aportado por el compañero.

**Resultado:** integración de código y recuperación técnica operativas; calidad
semántica pendiente de ajuste. No se ha validado una evaluación completa con
generación real de Qwen ni la interfaz en un navegador. No presentar esta prueba
como validación de la precisión de las respuestas.
