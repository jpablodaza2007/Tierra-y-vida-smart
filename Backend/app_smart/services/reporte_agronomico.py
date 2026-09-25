"""Generación del informe PDF persistible de la IA Agrónoma."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.utils import timezone


VERDE_OSCURO = '#0F4A34'
VERDE = '#2ECC71'
AZUL = '#0B131E'
GRIS_CLARO = '#F2F7F3'


def generar_reporte_agronomico(datos: dict, resultado: dict, nombre_campesino: str) -> bytes:
    """Construye un PDF de marca Tierra y Vida Smart listo para almacenar."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError as error:
        raise RuntimeError('Falta la dependencia reportlab para generar informes PDF.') from error

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=3.4 * cm,
        bottomMargin=1.8 * cm,
        title='Informe agronómico | Tierra y Vida Smart',
        author='Tierra y Vida Smart',
    )
    estilos_base = getSampleStyleSheet()
    estilos = {
        'titulo': ParagraphStyle('TituloTVS', parent=estilos_base['Title'], fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=colors.HexColor(AZUL), spaceAfter=6),
        'subtitulo': ParagraphStyle('SubtituloTVS', parent=estilos_base['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#557064'), spaceAfter=16),
        'seccion': ParagraphStyle('SeccionTVS', parent=estilos_base['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor(VERDE_OSCURO), spaceBefore=13, spaceAfter=6),
        'texto': ParagraphStyle('TextoTVS', parent=estilos_base['BodyText'], fontSize=10, leading=15, textColor=colors.HexColor('#24352B')),
        'centrado': ParagraphStyle('CentradoTVS', parent=estilos_base['Normal'], alignment=TA_CENTER, fontSize=9, leading=12, textColor=colors.HexColor('#557064')),
    }

    def parrafo(texto, estilo='texto'):
        return Paragraph(escape(str(texto or 'No disponible')).replace('\n', '<br/>'), estilos[estilo])

    def dato_etiquetado(etiqueta, valor):
        return Paragraph(
            f'<b>{escape(str(etiqueta))}</b><br/>{escape(str(valor or "No disponible"))}',
            estilos['texto'],
        )

    receta = resultado.get('receta_compost') or {}
    recomendaciones = resultado.get('recomendaciones_inmediatas') or []
    pasos = receta.get('instrucciones_armado') or []
    flujo = [
        Paragraph('Informe de diagnóstico agronómico', estilos['titulo']),
        parrafo(f'Preparado para {nombre_campesino} · Análisis asistido por IA Agrónoma', 'subtitulo'),
    ]

    estado = resultado.get('estado_salud_cultivo', 'Sin clasificación')
    fuente = 'Gemini IA' if resultado.get('fuente_diagnostico') == 'GEMINI' else 'Motor agronómico local'
    resumen = Table(
        [[dato_etiquetado('Estado del cultivo', estado), dato_etiquetado('Fuente del análisis', fuente)]],
        colWidths=[8.3 * cm, 8.3 * cm],
    )
    resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(GRIS_CLARO)),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#CDE9D5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CDE9D5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    flujo += [resumen, Spacer(1, 0.25 * cm), Paragraph('Resumen del diagnóstico', estilos['seccion']), parrafo(resultado.get('diagnostico_general'))]

    contexto = [
        ['Cultivo', datos.get('tipo_cultivo')], ['Fase', datos.get('fase_cultivo')],
        ['Área sembrada', f"{datos.get('area_cultivo_m2', 'No especificada')} m²"],
        ['Origen de datos', 'Sensores IoT' if datos.get('origen_datos') == 'SENSOR' else 'Registro manual'],
        ['Temperatura ambiental', f"{datos['temperatura']:.1f} C" if datos.get('temperatura') is not None else None],
        ['Humedad ambiental', f"{datos['humedad_ambiente']:.1f} %" if datos.get('humedad_ambiente') is not None else None],
        ['Humedad del suelo', f"{datos['humedad_suelo']:.1f} %" if datos.get('humedad_suelo') is not None else None],
        ['pH del suelo', f"{datos['ph_suelo']:.1f}" if datos.get('ph_suelo') is not None else None],
    ]
    tabla_contexto = Table([[dato_etiquetado(etiqueta, ''), parrafo(valor)] for etiqueta, valor in contexto], colWidths=[4.2 * cm, 12.4 * cm])
    tabla_contexto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E1F4E7')),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D8E5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    flujo += [Paragraph('Condiciones evaluadas', estilos['seccion']), tabla_contexto]

    compost = Table([[
        dato_etiquetado('Compost total', f"{receta.get('total_compost_requerido_kg', 0)} kg"),
        dato_etiquetado('Material verde', f"{receta.get('kg_material_verde', 0)} kg · 40 %"),
        dato_etiquetado('Material café', f"{receta.get('kg_material_cafe', 0)} kg · 60 %"),
    ]], colWidths=[5.53 * cm] * 3)
    compost.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(VERDE_OSCURO)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(VERDE_OSCURO)),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#4CA878')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    flujo += [Paragraph('Receta de compost sugerida', estilos['seccion']), compost]
    if pasos:
        flujo += [Paragraph('Armado paso a paso', estilos['seccion'])]
        flujo.extend(dato_etiquetado(f'{indice}.', paso) for indice, paso in enumerate(pasos, start=1))
    if recomendaciones:
        flujo += [Paragraph('Recomendaciones inmediatas', estilos['seccion'])]
        flujo.extend(dato_etiquetado('●', recomendacion) for recomendacion in recomendaciones)
    flujo += [Paragraph('Alerta fitosanitaria', estilos['seccion']), parrafo(resultado.get('alerta_plagas', 'NINGUNA'))]
    flujo += [Spacer(1, 0.25 * cm), parrafo('Este informe es una orientación técnica. Para decisiones de alto impacto, consulta a un profesional agrónomo local.', 'centrado')]

    logo = Path(settings.BASE_DIR).parent / 'Frontend' / 'public' / 'assets' / 'tierra-y-vida-logo.jpeg'

    def encabezado_y_pie(canvas, _doc):
        canvas.saveState()
        alto = A4[1]
        canvas.setFillColor(colors.HexColor(AZUL))
        canvas.rect(0, alto - 2.3 * cm, A4[0], 2.3 * cm, fill=1, stroke=0)
        if logo.exists():
            canvas.drawImage(str(logo), 1.7 * cm, alto - 1.83 * cm, width=1.25 * cm, height=1.25 * cm, preserveAspectRatio=True, mask='auto')
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(3.2 * cm, alto - 1.18 * cm, 'TIERRA Y VIDA')
        canvas.setFillColor(colors.HexColor(VERDE))
        canvas.drawString(6.85 * cm, alto - 1.18 * cm, 'SMART')
        canvas.setFillColor(colors.HexColor('#607265'))
        canvas.setFont('Helvetica', 8)
        canvas.drawCentredString(A4[0] / 2, 1.1 * cm, f'Tierra y Vida Smart · Informe generado el {timezone.localdate().strftime("%d/%m/%Y")} · Página {canvas.getPageNumber()}')
        canvas.restoreState()

    documento.build(flujo, onFirstPage=encabezado_y_pie, onLaterPages=encabezado_y_pie)
    return buffer.getvalue()
