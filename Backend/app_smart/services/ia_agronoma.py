"""Diagnóstico agronómico con Gemini y un motor local de respaldo.
"""

from __future__ import annotations

import json
import logging
import re
import ssl

from django.conf import settings

logger = logging.getLogger(__name__)

RANGOS_TEMPERATURA = {
    'papa': (14, 22), 'maíz': (18, 30), 'maiz': (18, 30),
    'frijol': (18, 28), 'hortalizas': (16, 25), 'café': (18, 24), 'cafe': (18, 24),
}
DOSIS_COMPOST_KG_M2 = {
    'papa': 1.5, 'maíz': 1.2, 'maiz': 1.2, 'frijol': 1.0,
    'hortalizas': 2.0, 'café': 1.3, 'cafe': 1.3,
}
MULTIPLICADOR_FASE = {
    'siembra': 1.15, 'crecimiento': 1.0, 'floración': .85,
    'floracion': .85, 'cosecha': .7,
}
ESTADOS_VALIDOS = {'Excelente', 'Atención Requerida', 'Crítico'}


def calcular_receta_compost(tipo_cultivo: str, fase_cultivo: str, area_m2: float) -> dict:
    """Calcula una mezcla 60 % café (carbono) / 40 % verde (nitrógeno)."""
    dosis = DOSIS_COMPOST_KG_M2.get(tipo_cultivo.lower(), 1.2)
    total = round(float(area_m2) * dosis * MULTIPLICADOR_FASE.get(fase_cultivo.lower(), 1.0), 2)
    cafe = round(total * .60, 2)
    verde = round(total - cafe, 2)
    return {
        'total_compost_requerido_kg': total,
        'kg_material_verde': verde,
        'kg_material_cafe': cafe,
        'instrucciones_armado': [
            'Ubica la compostera sobre suelo natural, en semisombra y con drenaje.',
            f'Alterna capas hasta usar {cafe} kg de material café y {verde} kg de material verde.',
            'Humedece cada capa hasta que la mezcla se sienta como una esponja escurrida.',
            'Voltea la pila cada 7 días y úsala cuando esté oscura y con olor a tierra.',
        ],
    }


def generar_diagnostico(datos: dict) -> dict:
    """Fallback explicable basado en reglas agronómicas básicas locales."""
    cultivo, fase = datos['tipo_cultivo'].strip(), datos['fase_cultivo'].strip()
    temperatura = datos.get('temperatura')
    humedad_suelo = datos.get('humedad_suelo')
    humedad_ambiente = datos.get('humedad_ambiente')
    ph = datos.get('ph_suelo')
    observaciones = (datos.get('observaciones_visuales') or '').lower()
    severidad, alertas, recomendaciones, plagas = 0, [], [], []
    min_temp, max_temp = RANGOS_TEMPERATURA.get(cultivo.lower(), (18, 28))
    if temperatura is not None:
        if temperatura < min_temp - 4 or temperatura > max_temp + 4:
            severidad = 2; alertas.append('La temperatura está fuera del rango tolerable.'); recomendaciones.append('Protege el cultivo con cobertura, sombra temporal o riego en horas frescas.')
        elif temperatura < min_temp or temperatura > max_temp:
            severidad = max(severidad, 1); alertas.append('La temperatura requiere seguimiento.')
    if humedad_suelo is not None:
        if humedad_suelo < 30:
            severidad = 2; alertas.append('El suelo presenta déficit hídrico crítico.'); recomendaciones.append('Riega gradualmente hoy y añade cobertura orgánica.')
        elif humedad_suelo < 50:
            severidad = max(severidad, 1); alertas.append('La humedad del suelo es baja.'); recomendaciones.append('Aumenta el riego aproximadamente 20 %, evitando escorrentía.')
        elif humedad_suelo > 85:
            severidad = max(severidad, 1); alertas.append('La humedad del suelo es excesiva.'); recomendaciones.append('Reduce el riego y revisa el drenaje.'); plagas.append('La humedad alta puede favorecer hongos radiculares y manchas foliares.')
    if ph is not None:
        if ph < 5.2 or ph > 7.5:
            severidad = 2; alertas.append('El pH limita la disponibilidad de nutrientes.'); recomendaciones.append('Solicita análisis de suelo y corrige el pH gradualmente con apoyo técnico local.')
        elif ph < 5.8 or ph > 7.0:
            severidad = max(severidad, 1); alertas.append('El pH está ligeramente fuera del rango recomendado.')
    if any(p in observaciones for p in ('amarill', 'clorosis')):
        severidad = max(severidad, 1); recomendaciones.append('Revisa humedad y pH; el amarillamiento puede indicar baja disponibilidad de nitrógeno.')
    if any(p in observaciones for p in ('mancha', 'hongo', 'mildiu', 'mildiú')):
        severidad = max(severidad, 1); plagas.append('Hay riesgo de enfermedad foliar; inspecciona el envés de las hojas y retira tejido muy afectado.')
    if any(p in observaciones for p in ('plaga', 'insecto', 'oruga', 'pulgón', 'pulgon')):
        severidad = max(severidad, 1); plagas.append('Posible presencia de plagas: realiza monitoreo visual y manejo integrado.')
    if not recomendaciones:
        recomendaciones.append('Mantén riego, cobertura del suelo y monitoreo semanal de las condiciones del cultivo.')
    recomendaciones.append('Incorpora el compost maduro alrededor de la planta sin tocar el tallo.')
    valores = ', '.join(x for x in [f'temperatura {temperatura:.1f} °C' if temperatura is not None else '', f'humedad ambiental {humedad_ambiente:.1f} %' if humedad_ambiente is not None else '', f'humedad del suelo {humedad_suelo:.1f} %' if humedad_suelo is not None else '', f'pH {ph:.1f}' if ph is not None else ''] if x) or 'sin mediciones numéricas'
    return {
        'estado_salud_cultivo': ('Excelente', 'Atención Requerida', 'Crítico')[severidad],
        'diagnostico_general': f'Para {cultivo} en fase de {fase}: {valores}. ' + (' '.join(alertas) if alertas else 'Las condiciones evaluadas son favorables.'),
        'receta_compost': calcular_receta_compost(cultivo, fase, datos['area_cultivo_m2']),
        'recomendaciones_inmediatas': recomendaciones,
        'alerta_plagas': ' '.join(plagas) if plagas else 'NINGUNA',
    }


def _extraer_json(texto: str) -> dict:
    """Acepta JSON puro o un bloque Markdown, pero rechaza respuestas incompletas."""
    coincidencia = re.search(r'\{.*\}', texto, re.DOTALL)
    respuesta = json.loads(coincidencia.group(0) if coincidencia else texto)
    requeridos = {'estado_salud_cultivo', 'diagnostico_general', 'receta_compost', 'recomendaciones_inmediatas', 'alerta_plagas'}
    if not requeridos.issubset(respuesta) or respuesta['estado_salud_cultivo'] not in ESTADOS_VALIDOS:
        raise ValueError('Gemini no devolvió el contrato esperado.')
    receta = respuesta['receta_compost']
    if not isinstance(receta, dict) or not {'total_compost_requerido_kg', 'kg_material_verde', 'kg_material_cafe', 'instrucciones_armado'}.issubset(receta):
        raise ValueError('Receta de compost incompleta.')
    return respuesta


def diagnosticar_cultivo(datos: dict) -> tuple[dict, str]:
    """Consulta Gemini y retorna ``(diagnóstico, fuente)``; jamás propaga errores externos."""
    fallback = generar_diagnostico(datos)
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return fallback, 'REGLAS_LOCALES'
    try:
        # Cliente oficial actual google-genai; se inicializa solo en Django.
        # Gemini 3.5 Flash está disponible para esta clave y soporta JSON.
        from google import genai
        from google.genai import types
        import httpx
        import truststore
        # En equipos Windows con proxy/antivirus corporativo se requiere el
        # almacén nativo de certificados; nunca se desactiva la verificación TLS.
        cliente_http = httpx.Client(
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
            timeout=30,
        )
        cliente = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30_000, httpx_client=cliente_http),
        )
        prompt = f'''Eres un agrónomo. Analiza estos datos: {json.dumps(datos, ensure_ascii=False)}.
Devuelve ESTRICTAMENTE JSON válido, sin Markdown ni texto extra, con esta estructura:
{{"estado_salud_cultivo":"Excelente|Atención Requerida|Crítico","diagnostico_general":"resumen conciso","receta_compost":{{"total_compost_requerido_kg":number,"kg_material_verde":number,"kg_material_cafe":number,"instrucciones_armado":["paso"]}},"recomendaciones_inmediatas":["consejo"],"alerta_plagas":"Descripción o NINGUNA"}}
Para la receta adapta al área indicada y mantén aproximadamente 60 % material café y 40 % material verde en peso (balance carbono/nitrógeno cercano a 30:1).'''
        # Un proveedor externo no debe retener la petición indefinidamente.
        # El timeout de 30 segundos del cliente activa el fallback local si falla.
        respuesta = cliente.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0.2,
                # La receta incluye listas e instrucciones; evita truncar el JSON.
                max_output_tokens=4096,
            ),
        )
        return _extraer_json(respuesta.text), 'GEMINI'
    except Exception as error:
        # El fallback es una condición controlada, no un traceback para el usuario.
        logger.warning('Gemini no estuvo disponible; se usó el motor local: %s', error)
        return fallback, 'REGLAS_LOCALES'
