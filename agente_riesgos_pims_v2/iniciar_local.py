"""Abre una instancia independiente sin detener procesos existentes."""
import argparse
import errno
import socket
import threading
import webbrowser

from werkzeug.serving import make_server
from app import app

# Puertos >= 1024 bloqueados por Chromium. No intentar eludir al navegador.
# Fuente: chromium/src/net/base/port_util.cc, kRestrictedPorts.
PUERTOS_RESTRINGIDOS = {
    1719, 1720, 1723, 2049, 3659, 4045, 5060, 5061, 6000,
    6566, 6665, 6666, 6667, 6668, 6669, 6697, 10080,
}


def iniciar():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--sin-navegador', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65515:
        parser.error('El puerto debe estar entre 1024 y 65515.')
    servidor = None
    for puerto in range(args.port, args.port + 21):
        if puerto in PUERTOS_RESTRINGIDOS:
            continue
        # Reservar el puerto antes de pasarlo a Werkzeug evita carreras al buscar uno libre.
        escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            escucha.bind(('127.0.0.1', puerto))
            escucha.listen(128)
        except OSError as exc:
            escucha.close()
            if exc.errno == errno.EADDRINUSE:
                continue
            raise
        try:
            servidor = make_server('127.0.0.1', puerto, app, threaded=True, fd=escucha.fileno())
        finally:
            escucha.close()
        break
    if servidor is None:
        parser.error('Los puertos del rango están ocupados. Usa --port con otro puerto.')
    url = f'http://127.0.0.1:{puerto}'
    print(f'Agente de riesgos v2: {url}', flush=True)
    print('Instancia independiente. Ctrl+C detiene únicamente esta instancia.', flush=True)
    if not args.sin_navegador:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == '__main__':
    iniciar()
