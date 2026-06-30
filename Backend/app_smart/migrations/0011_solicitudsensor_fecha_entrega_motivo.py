import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_smart', '0010_remove_usuario_ubicacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudsensor',
            name='fecha_entrega_deseada',
            field=models.DateField(default=django.utils.timezone.localdate),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='solicitudsensor',
            name='motivo_rechazo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
