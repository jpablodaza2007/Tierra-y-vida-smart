# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

TIPO_RESIDUO_CHOICES = [
    ('SECO', 'Residuo Seco (Cartón, Papel, Hojas secas, Aserrín)'),
    ('HUMEDO', 'Residuo Húmedo (Restos de frutas, verduras, café, orgánicos)'),
]

INVENTARIO_TIPO_CHOICES = [
    ('SECO', 'Seco'),
    ('HUMEDO', 'Húmedo'),
]

ESTADO_AUDITORIA_RESIDUO_CHOICES = [
    ('Pendiente', 'Pendiente'),
    ('Aceptado', 'Aceptado'),
    ('Rechazado', 'Rechazado'),
    ('PENDIENTE', 'Pendiente'),
    ('APROBADO', 'Aprobado'),
    ('RECHAZADO', 'Rechazado'),
    ('CONTRAOFERTA_ALCALDIA', 'Contraoferta de alcaldia'),
    ('ACEPTADO_POR_CONTRIBUYENTE', 'Aceptado por contribuyente'),
    ('ACEPTADO_POR_CAMPESINO', 'Aceptado por campesino'),
]

ESTADO_SOLICITUD_RESIDUO_CHOICES = [
    ('PENDIENTE', 'Pendiente'),
    ('APROBADO', 'Aprobado'),
    ('RECHAZADO', 'Rechazado'),
    ('CONTRAOFERTA_ALCALDIA', 'Contraoferta de alcaldia'),
    ('ACEPTADO_POR_CAMPESINO', 'Aceptado por campesino'),
]

ESTADO_DICTAMEN_CHOICES = [
    ('PENDIENTE', 'Pendiente'),
    ('ACEPTADO', 'Aceptado'),
    ('RECHAZADO', 'Rechazado'),
    ('activo', 'Activo'),
    ('pendiente_activacion', 'Pendiente de activacion'),
    ('pendiente_aprobacion', 'Pendiente de aprobacion'),
    ('aprobado', 'Aprobado'),
    ('rechazado', 'Rechazado'),
    ('EN_CAMINO', 'En camino'),
    ('ENTREGADO', 'Entregado'),
]

class Campesino(models.Model):
    id_campesino = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'campesino'
class Contribuyente(models.Model):
    id_contribuyente = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'contribuyente'


class Alcaldia(models.Model):
    id_alcaldia = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alcaldia'

class InventarioAlcaldia(models.Model):
    tipo_residuo = models.CharField(max_length=10, choices=INVENTARIO_TIPO_CHOICES, unique=True)
    cantidad_total_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        managed = True
        db_table = 'inventario_alcaldia'

class GestionLogistica(models.Model):
    id_gestion = models.AutoField(primary_key=True)
    id_usuario_alcaldia = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario_alcaldia', blank=True, null=True)
    id_residuo = models.OneToOneField('ResiduoOrganico', models.DO_NOTHING, db_column='id_residuo', blank=True, null=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    tipo_residuo = models.CharField(max_length=10, choices=INVENTARIO_TIPO_CHOICES, blank=True, null=True)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_asignacion = models.DateTimeField(blank=True, null=True)
    ubicacion_entrega = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'gestion_logistica'


class SolicitudResiduo(models.Model):
    id_solicitud_residuo = models.AutoField(primary_key=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    id_residuo = models.ForeignKey('ResiduoOrganico', models.DO_NOTHING, db_column='id_residuo', blank=True, null=True)
    tipo_residuo = models.CharField(max_length=20, choices=TIPO_RESIDUO_CHOICES, blank=True, null=True)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    precio_ofrecido_campesino = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    contraoferta_alcaldia = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    estado = models.CharField(max_length=30, choices=ESTADO_SOLICITUD_RESIDUO_CHOICES, default='PENDIENTE', blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'solicitud_residuo'


class DispositivoSensor(models.Model):
    """Dispositivo físico asignado a un campesino para enviar telemetría."""

    class ReferenciaHardware(models.TextChoices):
        ESP32_DHT22_TEMP = 'ESP32_DHT22_TEMP', 'ESP32 + DHT22 (temperatura y humedad)'
        ESP32_CAPACITIVO_HUMEDAD_SUELO = (
            'ESP32_CAPACITIVO_HUMEDAD_SUELO',
            'ESP32 + sensor capacitivo de humedad de suelo',
        )
        ESP32_PH_SUELO = 'ESP32_PH_SUELO', 'ESP32 + sensor de pH de suelo'

    class Estado(models.TextChoices):
        PENDIENTE_ENTREGA = 'PENDIENTE_ENTREGA', 'Pendiente de entrega'
        EN_CAMINO = 'EN_CAMINO', 'En camino'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        VINCULADO_ACTIVO = 'VINCULADO_ACTIVO', 'Vinculado y activo'

    codigo_mac = models.CharField(max_length=100, unique=True)
    campesino = models.ForeignKey('Usuario', on_delete=models.PROTECT, related_name='dispositivos_sensores')
    referencia_hardware = models.CharField(max_length=40, choices=ReferenciaHardware.choices)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.PENDIENTE_ENTREGA)
    fecha_vinculacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'dispositivo_sensor'

    def __str__(self):
        return self.codigo_mac


class LecturaSensor(models.Model):
    """Lectura normalizada recibida desde un dispositivo IoT."""

    id_lectura = models.AutoField(primary_key=True)
    dispositivo = models.ForeignKey(DispositivoSensor, on_delete=models.CASCADE, related_name='lecturas')
    temperatura_ambiente = models.FloatField(null=True, blank=True)
    humedad_ambiente = models.FloatField(null=True, blank=True)
    humedad_suelo_porcentaje = models.FloatField(null=True, blank=True)
    ph_suelo = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lectura_sensor'
        ordering = ['-timestamp']


class RecomendacionIa(models.Model):
    id_recomendacion = models.AutoField(primary_key=True)
    id_lectura = models.OneToOneField(LecturaSensor, models.DO_NOTHING, db_column='id_lectura', blank=True, null=True)
    mensaje_ia = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'recomendacion_ia'


class ResiduoOrganico(models.Model):
    id_residuo = models.AutoField(primary_key=True)
    id_contribuyente = models.ForeignKey(Contribuyente, models.DO_NOTHING, db_column='id_contribuyente', blank=True, null=True)
    tipo_residuo = models.CharField(max_length=20, choices=TIPO_RESIDUO_CHOICES, blank=True, null=True)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    peso_estimado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    precio_sugerido_contribuyente = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    contraoferta_alcaldia = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=30, choices=ESTADO_AUDITORIA_RESIDUO_CHOICES, default='PENDIENTE', blank=True)
    dias_almacenamiento = models.PositiveIntegerField(blank=True, null=True)
    metodo_conservacion = models.CharField(max_length=80, blank=True, null=True)
    lista_materiales = models.TextField(blank=True, null=True)
    presencia_citricos = models.CharField(max_length=80, blank=True, null=True)
    presencia_procesados = models.BooleanField(default=False)
    ausencia_origen_animal = models.BooleanField(default=False)
    presencia_plagas = models.CharField(max_length=50, blank=True, null=True)
    bolsa_compostable = models.BooleanField(default=False)
    tamano_picado = models.CharField(max_length=50, blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'residuo_organico'


class Sensor(models.Model):
    id_sensor = models.AutoField(primary_key=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    tipo_sensor = models.CharField(max_length=50, blank=True, null=True)
    id_solicitud_sensor = models.OneToOneField('SolicitudSensor', models.DO_NOTHING, db_column='id_solicitud_sensor', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sensor'


class SolicitudSensor(models.Model):
    id_solicitud_sensor = models.AutoField(primary_key=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    tipo_sensor = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADO_DICTAMEN_CHOICES, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_entrega_deseada = models.DateField()
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'solicitud_sensor'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=150)
    tipo_usuario = models.CharField(max_length=50, blank=True, null=True)
    comprobante_registro = models.FileField(
        upload_to='comprobantes/',
        blank=True,
        null=True,
    )
    estado_cuenta = models.CharField(
        max_length=30,
        choices=ESTADO_DICTAMEN_CHOICES,
        default='activo',
        blank=True,
    )

    class Meta:
        managed = True
        db_table = 'usuario'
