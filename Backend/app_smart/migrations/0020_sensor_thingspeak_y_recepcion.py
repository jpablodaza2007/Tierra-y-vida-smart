from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('app_smart', '0019_recomendacionia_historial_pdf')]

    operations = [
        migrations.AddField(model_name='sensor', name='thingspeak_channel_id', field=models.CharField(blank=True, max_length=50, null=True)),
        migrations.AddField(model_name='sensor', name='thingspeak_read_api_key', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='sensor', name='fecha_conexion_thingspeak', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='solicitudsensor', name='fecha_recepcion_confirmada', field=models.DateTimeField(blank=True, null=True)),
    ]
