"""Catálogo parcial 2025: títulos resumidos, sin reproducir requisitos de la norma."""
FUENTE = 'https://www.bsigroup.com/siteassets/pdf/th-th/products-and-services/th-as-cross-lg-ict-dt-iso27701-mp-iso27701revisionwebinar-1125.pdf'
# Código, tema resumido, rol, página del documento público BSI.
_DATOS = [
    ('A.1.2.2', 'Finalidad del tratamiento', 'responsable', 24),
    ('A.1.2.3', 'Base de legitimación', 'responsable', 24),
    ('A.1.3.10', 'Atención de solicitudes', 'responsable', 25),
    ('A.1.4.2', 'Limitación de la recogida', 'responsable', 26),
    ('A.1.4.8', 'Conservación', 'responsable', 26),
    ('A.2.2.2', 'Acuerdo con el cliente', 'encargado', 28),
    ('A.2.4.3', 'Devolución o eliminación', 'encargado', 29),
    ('A.3.7', 'Transferencia de información', 'ambos', 30),
    ('A.3.9', 'Permisos de acceso', 'ambos', 30),
    ('A.3.23', 'Autenticación segura', 'ambos', 32),
    ('A.3.24', 'Respaldos', 'ambos', 32),
    ('A.3.25', 'Registro de eventos', 'ambos', 32),
    ('A.3.26', 'Criptografía', 'ambos', 32),
]
CONTROLES = {codigo: dict(codigo=codigo, nombre=nombre, rol=rol,
    norma='ISO/IEC 27701:2025', anexo='A', guia='B' + codigo[1:],
    fuente=FUENTE + '#page=' + str(pagina)) for codigo, nombre, rol, pagina in _DATOS}


def catalogo_para_rol(rol):
    return {k: v for k, v in CONTROLES.items()
            if rol in ('ambos', 'no_definido') or v['rol'] in ('ambos', rol)}
