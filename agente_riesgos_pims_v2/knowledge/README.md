# Conocimiento del agente de riesgos

`controles_iso.py` contiene 13 referencias seleccionadas del anexo A de
ISO/IEC 27701:2025. Cada entrada identifica código, tema resumido, rol, guía B y
página del [material público de BSI](https://www.bsigroup.com/siteassets/pdf/th-th/products-and-services/th-as-cross-lg-ict-dt-iso27701-mp-iso27701revisionwebinar-1125.pdf).
Verificación de la numeración: 6 de octubre de 2026.

Este catálogo parcial no reproduce requisitos ni acredita cumplimiento. El
modelo debe justificar cada relación con el escenario y pedir evidencia para
verificarla. La selección de controles es revisable; no se infiere que los
controles omitidos no sean aplicables. Cualquier ampliación debe comprobar código,
edición, rol y fuente antes de incorporarse.

`documento_iso.py` recupera las guías legibles del archivo
`../../ISO_IEC_27701_2025.md`. Selecciona por temas y rol dentro del catálogo
parcial, conserva página OCR y línea y envía texto real al prompt. Valida que la
cita devuelta esté en un fragmento enviado. Se trata de recuperación documental
local por temas, complementada por el RAG híbrido de `../rag/` con embeddings
y FAISS sobre los archivos de `documentos/`. Los errores OCR se
conservan y deben contrastarse con el PDF original.
