# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
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

class GestionLogistica(models.Model):
    id_gestion = models.AutoField(primary_key=True)
    id_usuario_alcaldia = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario_alcaldia', blank=True, null=True)
    id_residuo = models.OneToOneField('ResiduoOrganico', models.DO_NOTHING, db_column='id_residuo', blank=True, null=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    fecha_asignacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'gestion_logistica'


class SolicitudResiduo(models.Model):
    id_solicitud_residuo = models.AutoField(primary_key=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    id_residuo = models.ForeignKey('ResiduoOrganico', models.DO_NOTHING, db_column='id_residuo', blank=True, null=True)
    estado = models.CharField(max_length=20, default='pendiente', blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'solicitud_residuo'


class LecturaSensor(models.Model):
    id_lectura = models.AutoField(primary_key=True)
    id_sensor = models.ForeignKey('Sensor', models.DO_NOTHING, db_column='id_sensor', blank=True, null=True)
    valor_lectura = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'lectura_sensor'


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
    tipo_residuo = models.CharField(max_length=100, blank=True, null=True)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'residuo_organico'


class Sensor(models.Model):
    id_sensor = models.AutoField(primary_key=True)
    id_campesino = models.ForeignKey(Campesino, models.DO_NOTHING, db_column='id_campesino', blank=True, null=True)
    tipo_sensor = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sensor'


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
        default='activo',
        blank=True,
    )

    class Meta:
        managed = True
        db_table = 'usuario'
