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
