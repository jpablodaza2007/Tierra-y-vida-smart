from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_smart', '0013_alter_solicitudresiduo_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='residuoorganico',
            name='latitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='longitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='solicitudresiduo',
            name='latitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='solicitudresiduo',
            name='longitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='sensor',
            name='id_solicitud_sensor',
            field=models.OneToOneField(blank=True, db_column='id_solicitud_sensor', null=True, on_delete=models.DO_NOTHING, to='app_smart.solicitudsensor'),
        ),
        migrations.AlterField(
            model_name='solicitudsensor',
            name='estado',
            field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('ACEPTADO', 'Aceptado'), ('RECHAZADO', 'Rechazado'), ('activo', 'Activo'), ('pendiente_activacion', 'Pendiente de activacion'), ('pendiente_aprobacion', 'Pendiente de aprobacion'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado'), ('EN_CAMINO', 'En camino'), ('ENTREGADO', 'Entregado')], default='PENDIENTE', max_length=20),
        ),
    ]
