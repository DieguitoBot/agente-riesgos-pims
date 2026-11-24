"""Anexa el contrato propio de reporte al formato académico; no modifica SQL."""
from datetime import date
from pathlib import Path
import shutil
from docx import Document
from knowledge.documento_pims import leer_docx
BASE=Path(__file__).resolve().parents[1]
RUTA=BASE/'knowledge/documentos/pims_unsa/PIMS-RIE-06_Informe_Evaluacion_Tratamiento.docx'
CAMPOS=[('Encabezado','UNSA · implementación académica simulada; sin aprobación institucional'),
('Identificador','UUID único de evaluación, compartido por API, reporte e historial'),
('Fecha y versión','Fecha UTC estable de evaluación; formato PIMS-RIE-06 / 1.0; documento de referencia revisión 0.3'),
('Estado','Borrador para revisión humana o borrador con alertas'),('Resumen ejecutivo','Valoración inicial, número de riesgos y límites de la evidencia'),
('Objetivo y alcance','Escenario declarado y límites; no extrapolar a toda la UNSA'),('Tratamiento','TRA y rol declarados; por confirmar si faltan'),
('Datos y activos','Categorías y ACT declarados; no completar con datos de otro tratamiento'),('Riesgo','Amenaza, vulnerabilidad, hecho e interpretación diferenciados'),
('Consecuencias','Titulares y efectos organizativos; no estimar sanciones o cifras sin evidencia'),('Probabilidad','Entero 1–5 asignado por usuario'),
('Impacto','Entero 1–5 asignado por usuario'),('Nivel','P × I y clasificación calculados por Python'),('Metodología','Bandas de PIMS-RIE-01; aceptación humana'),
('Controles','Selección contextual con cita; ninguna inclusión automática por coincidencia de nombre'),('Justificación','Hecho del escenario, relación normativa y decisión SoA'),
('Implementación','Propuesta/pendiente/verificada solo cuando exista evidencia'),('Plan','Medida, actividades y criterio de cierre; separado del análisis original'),
('Responsables y plazos','Por asignar/acordar si no existe registro humano'),('Residual estimado','No inferir reducción; hipótesis documentales separadas de resultados'),
('Aceptación residual','Pendiente de decisión documentada; no aceptar automáticamente'),('Evidencias','Versión, SHA256, fragmento y localizador; evidencia operativa si existe'),
('Referencias','Normativa, institucional e implementación PIMS; solo fuentes recuperadas y citas cotejadas'),('Conclusiones','Resultado inicial, revisión y límites de interpretación'),
('Recomendaciones','Acciones concretas y proporcionales; propuestas sujetas a revisión'),('Limitaciones','OCR, datos faltantes, inferencias, SoA abierta y falta de aprobación institucional')]
def main():
    anterior=leer_docx(RUTA)
    if '8. Estructura profesional del reporte dinámico' in anterior['contenido']:
        print('Formato RIE-06 0.3 sin cambios.');return
    respaldo=BASE/'datos/documentos_antes';respaldo.mkdir(parents=True,exist_ok=True)
    copia=respaldo/(RUTA.stem+'-'+anterior['metadatos']['sha256']+'.docx')
    if not copia.exists():shutil.copy2(RUTA,copia)
    d=Document(RUTA)
    for fila in d.tables[0].rows:
        if fila.cells[0].text=='Versión':fila.cells[1].text='0.3 — formato académico para revisión'
    for c,v in zip(d.tables[1].add_row().cells,[date.today().strftime('%d/%m/%Y'),'0.3','Contrato de 26 campos y estructura profesional de reporte; evidencia, cálculo e interpretación separados. Sin aprobación institucional.']):c.text=v
    d.add_heading('8. Estructura profesional del reporte dinámico',level=1)
    d.add_paragraph('Formato propio del proyecto, inspirado en los registros académicos. El anexo técnico conserva el análisis detallado. Las salidas TXT/CSV se mantienen; HTML aporta impresión y lectura estructurada, sin reproducir la norma privada.')
    t=d.add_table(rows=1,cols=2);t.style='Table Grid';t.rows[0].cells[0].text='Campo';t.rows[0].cells[1].text='Criterio de presentación'
    for nombre,criterio in CAMPOS:
        c=t.add_row().cells;c[0].text=nombre;c[1].text=criterio
    d.save(RUTA);print('Formato RIE-06 0.3 actualizado; campos:',len(CAMPOS))
if __name__=='__main__':main()
