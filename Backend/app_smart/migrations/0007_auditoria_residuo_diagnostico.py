# Generated for Tierra y Vida Smart audit flow

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_smart', '0006_gestionlogistica_ubicacion_entrega'),
    ]

    operations = [
        migrations.AlterField(
            model_name='residuoorganico',
            name='estado',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Pendiente', 'Pendiente'),
                    ('Aceptado', 'Aceptado'),
                    ('Rechazado', 'Rechazado'),
                ],
                default='Pendiente',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='dias_almacenamiento',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='metodo_conservacion',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='lista_materiales',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='presencia_citricos',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='presencia_procesados',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='ausencia_origen_animal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='presencia_plagas',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='bolsa_compostable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='tamano_picado',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='ubicacion',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='residuoorganico',
            name='motivo_rechazo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
