"""Suite determinista: impide conexiones a PostgreSQL y HTTP reales, incluso con .env."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import psycopg
import requests


def main():
    raiz = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(raiz))
    os.chdir(raiz)
    for opcion in ('LECTURA', 'DOCUMENTAL', 'CONSOLIDACION', 'EXPERIMENTO'):
        os.environ['PIMS_TEST_'+opcion] = '0'
    with patch('psycopg.connect', side_effect=psycopg.OperationalError('SQL real deshabilitado en unitarias')), \
         patch('requests.sessions.Session.request', side_effect=requests.ConnectionError('HTTP real deshabilitado en unitarias')):
        suite = unittest.defaultTestLoader.discover(str(raiz/'tests'))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName('tests_experimento'))
        resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
