import os

import django
from django.db import connection


def comprobar_conexion() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tierra_y_vida.settings')
    django.setup()

    print('Probando conexión a la base de datos de Tierra y Vida Smart...')

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()

        print('Conexión establecida correctamente con PostgreSQL.')
    except Exception as error:
        print('No fue posible conectar con PostgreSQL:')
        print(repr(error))
        raise


if __name__ == '__main__':
    comprobar_conexion()
