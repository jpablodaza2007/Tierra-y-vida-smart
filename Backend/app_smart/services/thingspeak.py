"""Lectura de la última medición DHT11 publicada en ThingSpeak."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _a_numero(valor):
    try:
        return float(valor) if valor is not None else None
    except (TypeError, ValueError):
        return None


def obtener_ultima_lectura_thingspeak():
    """Retorna temperatura y humedad ambiental, o ``None`` si no están disponibles."""
    channel_id = getattr(settings, 'THINGSPEAK_CHANNEL_ID', '')
    read_api_key = getattr(settings, 'THINGSPEAK_READ_API_KEY', '')
    if not channel_id:
        return None

    try:
        respuesta = requests.get(
            f'https://api.thingspeak.com/channels/{channel_id}/feeds/last.json',
            params={'api_key': read_api_key} if read_api_key else None,
            timeout=8,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        temperatura = _a_numero(datos.get('field1'))
        humedad_ambiente = _a_numero(datos.get('field2'))
        if temperatura is None and humedad_ambiente is None:
            logger.warning('ThingSpeak no devolvió temperatura ni humedad en el último registro.')
            return None
        return {
            'temperatura': temperatura,
            'humedad_ambiente': humedad_ambiente,
        }
    except (requests.RequestException, ValueError) as error:
        logger.warning('No se pudo leer ThingSpeak: %s', error)
        return None
