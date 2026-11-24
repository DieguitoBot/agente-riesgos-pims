"""Genera revisión académica 0.3 de la SoA desde el OCR privado, sin escribir SQL.

Requiere python-docx. Preserva copia de la fuente anterior en datos/, fuera de Git.
No incorpora texto normativo: solo resúmenes y decisiones académicas propias.
"""
from collections import Counter
from datetime import date
import hashlib
from pathlib import Path
import shutil

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from knowledge.documento_iso import leer_secciones, DOCUMENTO
from knowledge.documento_pims import leer_docx
from knowledge.revision_soa import revisar

BASE=Path(__file__).resolve().parents[1]
RUTA=BASE/'knowledge/documentos/pims_unsa/PIMS-RIE-04_SoA_Extracto.docx'
CABECERAS=['Control','Nombre resumido','Aplicabilidad','Justificación','Riesgos','Implementación','Evidencia','Acciones','Observaciones','Fuente']


def main():
    secciones,huella=leer_secciones(DOCUMENTO)
    filas=revisar(secciones,huella)
    anterior=leer_docx(RUTA)
    valores=[[r[c] for c in ('codigo','nombre','aplicabilidad','justificacion','riesgos','estado','evidencia','acciones','observaciones','fuente')] for r in filas]
    existentes=[fila for tabla in anterior['tablas'] if tabla and tabla[0]==CABECERAS for fila in tabla[1:]]
    if existentes==valores:
        print('SoA 0.3 sin cambios; se conserva su huella.');return
    respaldo=BASE/'datos/documentos_antes';respaldo.mkdir(parents=True,exist_ok=True)
    copia=respaldo/(RUTA.stem+'-'+anterior['metadatos']['sha256']+'.docx')
    if not copia.exists():shutil.copy2(RUTA,copia)
    historia=anterior['tablas'][1]
    d=Document(RUTA)
    for nodo in list(d._element.body):
        if nodo.tag!=qn('w:sectPr'):d._element.body.remove(nodo)
    sec=d.sections[0];sec.orientation=WD_ORIENT.LANDSCAPE
    sec.page_width=Cm(42);sec.page_height=Cm(29.7)
    sec.top_margin=sec.bottom_margin=Cm(1.5);sec.left_margin=sec.right_margin=Cm(1.4)
    normal=d.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(9)
    normal.paragraph_format.space_after=Pt(4)
    d.add_heading('UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA',0)
    d.add_heading('Declaración de Aplicabilidad — revisión sistemática de controles',1)
    d.add_paragraph('IMPLEMENTACIÓN ACADÉMICA SIMULADA · no aprobada por la UNSA')
    meta=d.add_table(rows=0,cols=2);meta.style='Table Grid'
    for k,v in [('Código','PIMS-RIE-04'),('Versión','0.3 — revisión académica sistemática'),
      ('Fecha',date.today().strftime('%d/%m/%Y')),('Elaboración','Equipo del Agente de Evaluación de Riesgos — por revisar'),
      ('Aprobación institucional','PENDIENTE. Sin aprobación de la UNSA.'),('Clasificación','SIMULADO · uso académico · sin datos reales'),
      ('Referencias','ISO/IEC 27701:2025: 6.1.3, tablas A.1/A.2/A.3 y guías del Anexo B; OCR autorizado con cotejo PDF pendiente')]:
        c=meta.add_row().cells;c[0].text=k;c[1].text=v
    d.add_heading('Historial de cambios',2)
    t=d.add_table(rows=0,cols=3);t.style='Table Grid'
    for fila in historia:
        for c,v in zip(t.add_row().cells,fila):c.text=v
    for c,v in zip(t.add_row().cells,[date.today().strftime('%d/%m/%Y'),'0.3','Revisión sistemática de 78 controles por alcance y rol. Se preservan decisiones pendientes; no se acreditan implementación ni conformidad.']):c.text=v
    d.add_heading('1. Objetivo, alcance y criterio de revisión',2)
    d.add_paragraph('Se revisan los 78 identificadores corroborados mediante guías B: 31 de A.1, 18 de A.2 y 29 de A.3. Alcance: TRA-001 matrícula, TRA-002 bienestar y TRA-003 biblioteca. Los roles responsable/encargado deben confirmarse según PIMS-RIE-05B; no se presumen operaciones de encargado ni proveedores reales.')
    d.add_paragraph('Fuentes de contexto: PIMS-RIE-01, PIMS-RIE-02, PIMS-RIE-03, PIMS-RIE-03A, PIMS-RIE-05A, PIMS-RIE-05B, PIMS-RIE-07 y PIMS-RIE-21. RIE-001/002/003 y ACC-001 a ACC-005 son supuestos académicos, no incidentes o decisiones institucionales.')
    d.add_heading('2. Criterios normativos y limitaciones de OCR',2)
    d.add_paragraph('6.1.3 orienta selección de opciones, controles necesarios, programa de seguridad, contraste con Anexo A, justificación de inclusiones/exclusiones, plan y aprobación humana de su aceptación residual. Se consideran las orientaciones B, sin confundir una guía recuperada con evidencia de implementación.')
    d.add_paragraph('Fuente privada SHA256 '+huella+'. Se conserva intacta. Los códigos A de las tablas OCR están deteriorados; se corroboran mediante la correspondencia explícita A/B. B.14.4 se identifica como B.1.4.4 por estructura y título, sin alterar el texto. La enumeración de 6.1.3 y las tablas A requieren cotejo con PDF autorizado.')
    d.add_heading('3. Resumen de decisiones',2)
    resumen=Counter(r['aplicabilidad'] for r in filas)
    d.add_paragraph('; '.join(f'{k}: {v}' for k,v in resumen.items())+'. Ninguna exclusión definitiva, implementación o aceptación se presume. Las decisiones PENDIENTES DE ANÁLISIS requieren datos de alcance, roles, riesgos, contratos y revisión humana.')
    d.add_paragraph('La cobertura de revisión es sistemática; la SoA sigue siendo un borrador con decisiones abiertas. No es una declaración institucional completa o aprobada. Los plazos, propietarios y evidencias operativas faltantes se registran como pendientes.')
    for tabla in ('A.1','A.2','A.3'):
        d.add_heading('4. Revisión '+tabla,2)
        t=d.add_table(rows=1,cols=len(CABECERAS));t.style='Table Grid';t.autofit=False
        for c,v in zip(t.rows[0].cells,CABECERAS):c.text=v
        header=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(header)
        for fila,val in zip(filas,valores):
            if not fila['codigo'].startswith(tabla+'.'):continue
            for c,v in zip(t.add_row().cells,val):c.text=v
        for row in t.rows:
            for cell,ancho in zip(row.cells,(1.6,2.7,2.6,5.8,2.7,3,3.4,3.3,6,5.9)):
                cell.width=Cm(ancho)
    d.add_heading('5. Aprobación, evidencias y mantenimiento',2)
    d.add_paragraph('Aprobación del plan: pendiente. Aceptación residual: pendiente. No hay evidencia operativa. Revisar inclusiones y posibles exclusiones al confirmar el alcance y roles; aprobar por el propietario simulado y revalidar ante cambios. Las acciones por programar no se consideran ACC ejecutadas. Responsable propuesto y recursos: por acordar, sin atribuir decisiones reales a la UNSA.')
    d.core_properties.title='PIMS-RIE-04 · SoA académica revisión 0.3';d.core_properties.subject='SIMULACIÓN ACADÉMICA'
    d.save(RUTA)
    print('SoA actualizada:',len(filas),'controles;',dict(resumen))
    print('SHA256:',hashlib.sha256(RUTA.read_bytes()).hexdigest())


if __name__=='__main__':main()
