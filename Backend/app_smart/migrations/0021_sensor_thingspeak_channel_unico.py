from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('app_smart', '0020_sensor_thingspeak_y_recepcion')]

    operations = [
        migrations.AddConstraint(
            model_name='sensor',
            constraint=models.UniqueConstraint(
                fields=('thingspeak_channel_id',),
                condition=models.Q(thingspeak_channel_id__isnull=False) & ~models.Q(thingspeak_channel_id=''),
                name='sensor_thingspeak_channel_unico',
            ),
        ),
    ]
