"""Acceso a fuentes privadas: interfaz local o credencial de servicio explícita."""
from functools import wraps
from hmac import compare_digest
from ipaddress import ip_address
import os
from urllib.parse import urlsplit

from flask import jsonify, make_response, request


def _loopback(valor):
    try:
        direccion = ip_address(valor)
        return direccion.is_loopback or bool(
            getattr(direccion, 'ipv4_mapped', None) and direccion.ipv4_mapped.is_loopback)
    except ValueError:
        return False


def _local():
    if os.getenv('PIMS_DOCUMENTOS_LOCAL', '1') != '1':
        return False
    # No confiar en Host arbitrario ni en X-Forwarded-For suministrado por el cliente.
    try:
        host = urlsplit(request.host_url).hostname
    except ValueError:
        return False
    if not (_loopback(request.remote_addr or '') and
            (host == 'localhost' or _loopback(host or ''))):
        return False
    # Un proxy puede llegar por loopback: exigir token si anuncia intermediación.
    if any(h in request.headers for h in ('Forwarded', 'X-Forwarded-For', 'X-Forwarded-Host')):
        return False
    origen = request.headers.get('Origin')
    return not origen or origen == request.host_url.rstrip('/')


def acceso_documental(vista):
    @wraps(vista)
    def protegida(*args, **kwargs):
        token = os.getenv('PIMS_DOCUMENTOS_TOKEN', '')
        autorizacion = request.headers.get('Authorization', '')
        autenticado = bool(token) and compare_digest(
            autorizacion.encode('utf-8'), ('Bearer ' + token).encode('utf-8'))
        if not (_local() or autenticado):
            respuesta = make_response(jsonify(error='Acceso documental no autorizado.'), 401)
            respuesta.headers['WWW-Authenticate'] = 'Bearer'
        else:
            respuesta = make_response(vista(*args, **kwargs))
        respuesta.headers['Cache-Control'] = 'no-store, private'
        respuesta.headers['X-Content-Type-Options'] = 'nosniff'
        respuesta.headers['Referrer-Policy'] = 'no-referrer'
        return respuesta
    return protegida
