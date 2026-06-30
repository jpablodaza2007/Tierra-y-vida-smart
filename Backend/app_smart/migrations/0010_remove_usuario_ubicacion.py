from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_smart', '0009_usuario_tipo_usuario_admin_check'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='ubicacion',
        ),
    ]
