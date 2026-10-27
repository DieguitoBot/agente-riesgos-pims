"""Documento sintético para probar el lector OCR; no reproduce la norma ISO."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ACCESO = 'Synthetic access profiles for individual user access IDs.'
RETENCION = 'Synthetic retention guidance for test records only.'


def instalar_iso_sintetico(caso):
    temporal = TemporaryDirectory()
    caso.addCleanup(temporal.cleanup)
    ruta = Path(temporal.name, 'iso_sintetico.md')
    secciones = [
        ('### B.3.9 Access rights', ACCESO),
        ('### B.3.10 Next section', 'Synthetic next section.'),
        ('B.1.2.3. Consent example', 'Synthetic consent example.'),
        ('B.2.4.3_ Return example', 'Synthetic return example.'),
        ('### B.1.4.8 Retention example', RETENCION),
        ('### B.3.24 Backup example', 'Synthetic backup example.'),
    ]
    ruta.write_text('## Annex B\n<!-- Page 48 -->\n' + '\n'.join(
        f'{titulo}\nControl\n{texto}\nImplementation guidance\nTest content.\n'
        for titulo, texto in secciones) + '\n## Annex C\n', encoding='utf-8')
    parche = patch('knowledge.documento_iso.DOCUMENTO', ruta)
    parche.start()
    caso.addCleanup(parche.stop)
