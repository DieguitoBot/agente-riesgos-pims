# Recuperación documental de V3

Desde `agente_riesgos_pims_v3/`, con su entorno y PostgreSQL preparado:

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-rag.txt
ollama pull embeddinggemma
.venv/bin/python -m db.migrar
.venv/bin/python -m rag.indexar
.venv/bin/python -m rag.probar "Acceso no autorizado a datos de estudiantes"
```

Documentos y vectores viven en PostgreSQL. La búsqueda combina términos BM25
con similitud coseno de embeddings locales. Si Ollama no responde, conserva la
búsqueda por términos; si PostgreSQL no está disponible, lo informa sin fabricar
fuentes. Ya no se requieren FAISS, índices en disco ni una segunda aplicación.

Para cargar fuentes se usa la conexión administrativa de mantenimiento; las
consultas HTTP usan el rol limitado. Tras cambiar fuentes, migrar y reindexar.
No distribuir normativa privada ni considerar una coincidencia como dictamen.

El paquete `pims_unsa/*.docx` se fragmenta por párrafos y filas con sus cabeceras,
conservando código, versión, huella y localizador XML. La numeración es local a
cada documento, independiente de añadir otras fuentes. Los identificadores
TRA/ACT/RIE/ACC y PIMS-RIE se buscan completos. Durante una evaluación se reserva
un fragmento para los criterios de PIMS-RIE-01; se marca como selección por
metodología, con sus puntajes reales, sin fingir relevancia semántica.

`GET /api/documentos` muestra metadatos y cantidad de fragmentos con vectores.
`GET /api/fuente-rag/<sha256>/<fragmento>` devuelve la fuente de PostgreSQL,
incluidas versiones anteriores archivadas. El conteo de vectores no prueba por
sí solo pertinencia: `validar_pims.py` consulta los diez documentos y ejecuta
evaluaciones reales, con cotejo literal de citas y exportación de reportes.


La ISO privada ahora se fragmenta en PostgreSQL como secciones `iso` y como
fragmentos `rag` con embeddings: 86 secciones (incluye cláusulas y tablas A) y
120 fragmentos semánticos. No se lee el archivo normativo durante evaluaciones.
B.14.4 se reconoce como B.1.4.4 con anotación de corrección; el texto OCR permanece
literal y la validación con PDF sigue pendiente. El catálogo resume 78 controles,
pero su selección contextual no acredita aplicabilidad o implementación.

La SoA se consulta en PostgreSQL para mostrar decisión, justificación y estado
por control relacionado. No se agrega una cuota de referencias de cada categoría.
Las versiones y huellas de normativa, institucionales y PIMS acompañan la lectura;
una versión no declarada se presenta como tal. La actualización selectiva se hace
con `db.migrar --solo`, seguida de indexación de fragmentos pendientes.
