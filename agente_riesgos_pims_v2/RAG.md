# RAG con Ollama + FAISS

## Instalar (Ubuntu, desde agente_riesgos_pims_v2)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-rag.txt
ollama pull qwen3.5:4b-q4_K_M
ollama pull embeddinggemma
```

Asegúrate de que el servicio Ollama esté activo (`sudo systemctl start ollama` o `ollama serve`, pero no ambos).

Coloca PDF con texto o archivos TXT/MD en `knowledge/documentos/`. Usa normativa oficial vigente; no publiques datos personales ni textos ISO protegidos por licencia.

```bash
python -m rag.indexar
python -m rag.probar "Una universidad publica DNI sin control de acceso"
python app.py
```

En `POST /api/evaluar` se agregan los campos `estado_rag` y `fuentes_rag` (archivo, página y similitud). El modelo recibe hasta cuatro fragmentos, tratados solo como datos. Si falta el índice o falla el modelo, la evaluación habitual continúa.

No se garantiza que la recuperación vectorial demuestre infracción normativa; toda cita debe verificarse contra el documento original. Los índices se almacenan solo localmente en `rag/indice_local/`; no subirlos al repositorio. Al cambiar fuentes o modelo de embeddings, ejecutar nuevamente el indexador.
