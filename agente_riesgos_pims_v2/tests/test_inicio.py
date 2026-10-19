import errno
import unittest
from unittest.mock import patch

from iniciar_local import iniciar


class TestInicio(unittest.TestCase):
    def test_omite_puertos_restringidos_al_buscar_puerto_libre(self):
        with patch('sys.argv', ['iniciar_local.py', '--port', '5058', '--sin-navegador']), \
             patch('iniciar_local.socket.socket') as socket, \
             patch('iniciar_local.make_server') as servidor, patch('builtins.print'):
            socket.return_value.bind.side_effect = [
                OSError(errno.EADDRINUSE, 'Ocupado'), OSError(errno.EADDRINUSE, 'Ocupado'), None]
            iniciar()
            self.assertEqual([c.args[0][1] for c in socket.return_value.bind.call_args_list],
                             [5058, 5059, 5062])
            self.assertEqual(servidor.call_args.args[1], 5062)
            servidor.return_value.serve_forever.assert_called_once()
            servidor.return_value.server_close.assert_called_once()

    def test_puerto_predeterminado_8080(self):
        with patch('sys.argv', ['iniciar_local.py', '--sin-navegador']), \
             patch('iniciar_local.socket.socket') as socket, \
             patch('iniciar_local.make_server'), patch('builtins.print'):
            iniciar()
            socket.return_value.bind.assert_called_once_with(('127.0.0.1', 8080))
