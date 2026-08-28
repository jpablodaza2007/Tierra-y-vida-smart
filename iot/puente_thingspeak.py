"""Puente USB: recibe JSON del Arduino y lo publica en ThingSpeak."""

import argparse
import json
import sys
import time

import requests
import serial
from serial.tools import list_ports


def argumentos():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, help='Puerto del Arduino, por ejemplo COM3.')
    parser.add_argument('--channel', required=True, help='ID numérico del canal ThingSpeak.')
    parser.add_argument('--write-key', required=True, help='Write API Key del canal ThingSpeak.')
    parser.add_argument('--baud', type=int, default=9600)
    parser.add_argument('--verbose', action='store_true', help='Muestra cada línea recibida del Arduino.')
    parser.add_argument('--probar-thingspeak', action='store_true', help='Publica 25 °C y 60 % sin abrir el puerto USB.')
    return parser.parse_args()


def publicar(channel, write_key, lectura):
    respuesta = requests.post(
        'https://api.thingspeak.com/update.json',
        json={
            'api_key': write_key,
            'field1': lectura['temperatura'],
            'field2': lectura['humedad_ambiente'],
        },
        timeout=15,
    )
    try:
        datos_respuesta = respuesta.json()
    except ValueError:
        datos_respuesta = respuesta.text
    if not respuesta.ok:
        raise RuntimeError(f'ThingSpeak respondió HTTP {respuesta.status_code}: {datos_respuesta}')
    if not isinstance(datos_respuesta, dict) or datos_respuesta.get('entry_id') is None:
        raise RuntimeError(
            'ThingSpeak rechazó la medición. Respuesta recibida: '
            f'{datos_respuesta}. Revisa la Write API Key y espera al menos 15 segundos entre envíos.'
        )
    return datos_respuesta['entry_id']


def puertos_disponibles():
    puertos = [f'{puerto.device} ({puerto.description})' for puerto in list_ports.comports()]
    return ', '.join(puertos) if puertos else 'ninguno'


def main():
    args = argumentos()
    print(f'Iniciando puente: canal {args.channel}, puerto {args.port}, {args.baud} baudios.', flush=True)

    if args.probar_thingspeak:
        try:
            entrada = publicar(args.channel, args.write_key, {'temperatura': 25, 'humedad_ambiente': 60})
            print(f'Prueba exitosa. ThingSpeak creó la entrada #{entrada}.', flush=True)
        except (requests.RequestException, RuntimeError) as error:
            print(f'Error exacto al publicar en ThingSpeak: {error}', file=sys.stderr, flush=True)
            raise SystemExit(1)
        return

    try:
        puerto = serial.Serial(args.port, args.baud, timeout=2)
    except serial.SerialException as error:
        print(
            f'No se pudo abrir {args.port}: {error}. Puertos detectados: {puertos_disponibles()}. '
            'Cierra el Monitor Serie y confirma el puerto en Arduino IDE.',
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)

    with puerto:
        time.sleep(2)  # El Uno se reinicia al abrir el puerto serie.
        print(f'Puente activo en {args.port}. Esperando una línea JSON del Arduino...', flush=True)
        ultima_linea = time.monotonic()
        while True:
            linea = puerto.readline().decode('utf-8', errors='replace').strip()
            if not linea:
                if time.monotonic() - ultima_linea >= 10:
                    print('Aún no llega información por USB. Verifica el cable, COM y que el Monitor Serie esté cerrado.', flush=True)
                    ultima_linea = time.monotonic()
                continue
            ultima_linea = time.monotonic()
            if args.verbose:
                print(f'USB recibió: {linea}', flush=True)
            try:
                lectura = json.loads(linea)
                temperatura = float(lectura['temperatura'])
                humedad = float(lectura['humedad_ambiente'])
                if not (-40 <= temperatura <= 80 and 0 <= humedad <= 100):
                    raise ValueError('Valores DHT11 fuera de rango.')
                entrada = publicar(args.channel, args.write_key, {
                    'temperatura': temperatura,
                    'humedad_ambiente': humedad,
                })
                print(f'Publicado en ThingSpeak (entrada #{entrada}): {temperatura:.1f} °C, {humedad:.1f} %', flush=True)
            except (KeyError, ValueError, json.JSONDecodeError) as error:
                print(f'Línea descartada ({error}): {linea}', file=sys.stderr, flush=True)
            except (requests.RequestException, RuntimeError) as error:
                print(f'Error exacto al publicar en ThingSpeak: {error}', file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()
