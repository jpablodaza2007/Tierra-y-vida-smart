from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_smart', '0014_sensor_lifecycle_and_geolocation'),
    ]

    operations = [
        migrations.CreateModel(
            name='DispositivoSensor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_mac', models.CharField(max_length=100, unique=True)),
                ('referencia_hardware', models.CharField(choices=[('ESP32_DHT22_TEMP', 'ESP32 + DHT22 (temperatura y humedad)'), ('ESP32_CAPACITIVO_HUMEDAD_SUELO', 'ESP32 + sensor capacitivo de humedad de suelo'), ('ESP32_PH_SUELO', 'ESP32 + sensor de pH de suelo')], max_length=40)),
                ('estado', models.CharField(choices=[('PENDIENTE_ENTREGA', 'Pendiente de entrega'), ('EN_CAMINO', 'En camino'), ('ENTREGADO', 'Entregado'), ('VINCULADO_ACTIVO', 'Vinculado y activo')], default='PENDIENTE_ENTREGA', max_length=25)),
                ('fecha_vinculacion', models.DateTimeField(blank=True, null=True)),
                ('campesino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dispositivos_sensores', to='app_smart.usuario')),
            ],
            options={
                'db_table': 'dispositivo_sensor',
            },
        ),
        migrations.RemoveField(
            model_name='lecturasensor',
            name='fecha_hora',
        ),
        migrations.RemoveField(
            model_name='lecturasensor',
            name='id_sensor',
        ),
        migrations.RemoveField(
            model_name='lecturasensor',
            name='valor_lectura',
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='dispositivo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lecturas', to='app_smart.dispositivosensor'),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='humedad_ambiente',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='humedad_suelo_porcentaje',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='ph_suelo',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='temperatura_ambiente',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterModelOptions(
            name='lecturasensor',
            options={'ordering': ['-timestamp']},
        ),
    ]
