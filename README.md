# Proyección de costos — Tierra y Vida Smart (2027)

Estimación académica para seis meses de desarrollo y tres meses de mantenimiento posterior. El alcance incluye una plataforma Angular y Django con usuarios campesinos, contribuyentes y alcaldías; gestión de residuos y logística; solicitudes de sensores; recomendaciones agronómicas y PDF; y telemetría IoT mediante Arduino Uno, DHT11 y ThingSpeak.

## 16.1 Talento humano

| Rol | Descripción | Dedicación estimada | Valor por hora | Subtotal |
| --- | --- | ---: | ---: | ---: |
| Analista de requerimientos | Requisitos, historias de usuario y reglas de negocio para los tres tipos de usuario. | 12 h/mes × 6 = 72 h | $15.000 | $1.080.000 |
| Diseñador UI/UX | Navegación e interfaces responsivas para autenticación y paneles por rol. | 12 h/mes × 6 = 72 h | $20.000 | $1.440.000 |
| Desarrollador frontend | Angular: formularios, paneles, validaciones, consumo de API y telemetría. | 24 h/mes × 6 = 144 h | $30.000 | $4.320.000 |
| Desarrollador backend | Django: API, modelos, permisos, logística, IA, PDF e integración ThingSpeak. | 26 h/mes × 6 = 156 h | $30.000 | $4.680.000 |
| Tester o QA | Pruebas de roles, residuos, solicitudes, sensores, telemetría y reportes. | 14 h/mes × 6 = 84 h | $20.000 | $1.680.000 |
| Líder del proyecto | Planeación, seguimiento, integración y puesta en marcha. | 12 h/mes × 6 = 72 h | $25.000 | $1.800.000 |

**Subtotal talento humano: $15.000.000 COP**

## 16.2 Herramientas tecnológicas

| Herramienta o recurso | Descripción | Tipo de costo | Tiempo | Subtotal |
| --- | --- | --- | ---: | ---: |
| Visual Studio Code, GitHub, Angular CLI, Django y Python | Herramientas de desarrollo, control de versiones, framework frontend, backend y lenguaje de programación. | Gratuito / código abierto | 6 meses | $0 |
| ThingSpeak | Plataforma para recibir, almacenar y visualizar la telemetría enviada por el Arduino y el sensor DHT11. | Plan gratuito | 6 meses | $0 |
| Dominio web | Dirección web para publicar y acceder a la plataforma Tierra y Vida Smart. | Proyectado | 1 año | $60.000 |
| Hosting básico / VPS | Servidor para alojar la aplicación Angular, la API Django y la base de datos. | Proyectado ($45.000/mes) | 6 meses | $270.000 |
| Internet asignado al proyecto | Conectividad usada durante el desarrollo, pruebas, despliegue y transmisión de datos IoT. | Estimado ($80.000/mes) | 6 meses | $480.000 |

**Subtotal herramientas tecnológicas: $810.000 COP**

## 16.3 Infraestructura y equipos

| Recurso | Descripción | Cantidad | Valor unitario | Subtotal |
| --- | --- | ---: | ---: | ---: |
| Computadores portátiles | Equipos para programación, diseño, pruebas y administración de la plataforma. | 3 | Recurso disponible | $0 |
| Celulares Android | Dispositivos para probar la versión responsiva y los flujos de usuarios en campo. | 2 | Recurso disponible | $0 |
| Arduino Uno | Microcontrolador que captura y transmite las mediciones del sensor ambiental. | 1 | $70.000 | $70.000 |
| Sensor DHT11 | Sensor para medir temperatura y humedad del entorno agrícola. | 1 | $20.000 | $20.000 |
| Protoboard, cables USB y jumpers | Material de conexión y prototipado para integrar el Arduino con el sensor. | 1 | $25.000 | $25.000 |
| Memoria USB | Medio para respaldos, instaladores y traslado de evidencias del proyecto. | 1 | $30.000 | $30.000 |

**Subtotal infraestructura y equipos: $145.000 COP**

## 16.4 Pruebas

El diseño de casos, pruebas manuales y automatizadas, evidencias, reporte de errores y validación final están incluidos en las horas del Tester o QA. No hay costo externo adicional.

**Subtotal pruebas: $0 COP**

## 16.5 Documentación

El documento de análisis, documento técnico, manuales de usuario y técnico, informe de pruebas y consolidación final están incluidos en las horas de talento humano.

**Subtotal documentación: $0 COP**

## 16.6 Despliegue y puesta en marcha

La configuración del hosting, API Django, base de datos, autenticación, pruebas de despliegue y capacitación básica están incluidos en talento humano. El dominio y hosting se contabilizan en herramientas tecnológicas.

**Subtotal despliegue y puesta en marcha: $0 COP**

## 16.7 Mantenimiento

| Actividad de mantenimiento | Horas estimadas / mes | Valor mensual estimado | Tiempo proyectado | Subtotal |
| --- | ---: | ---: | ---: | ---: |
| Corrección de errores | 8 h | $120.000 | 3 meses | $360.000 |
| Ajustes menores | 8 h | $120.000 | 3 meses | $360.000 |
| Actualización de contenido o datos | 6 h | $90.000 | 3 meses | $270.000 |
| Soporte a usuarios | 6 h | $90.000 | 3 meses | $270.000 |
| Revisión de seguridad básica | 4 h | $60.000 | 3 meses | $180.000 |

**Subtotal mantenimiento: $1.440.000 COP**

## 16.8 Resumen general

| Categoría | Valor estimado |
| --- | ---: |
| Talento humano | $15.000.000 |
| Herramientas tecnológicas | $810.000 |
| Infraestructura y equipos | $145.000 |
| Pruebas | $0 (incluido en talento humano) |
| Documentación | $0 (incluido en talento humano) |
| Despliegue y puesta en marcha | $0 (incluido en talento humano) |
| Mantenimiento | $1.440.000 |
| **Subtotal general** | **$17.395.000** |
| Imprevistos (10 %) | $1.739.500 |
| **Total proyectado** | **$19.134.500** |

La estimación evita duplicar la mano de obra: pruebas, documentación y despliegue ya están valorados en talento humano; solo se contabilizan aparte gastos externos reales.
