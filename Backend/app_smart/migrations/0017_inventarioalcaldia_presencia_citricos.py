from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_smart', '0016_alter_usuario_estado_cuenta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventarioalcaldia',
            name='tipo_residuo',
            field=models.CharField(choices=[('SECO', 'Seco'), ('HUMEDO', 'Humedo')], max_length=10),
        ),
        migrations.AddField(
            model_name='inventarioalcaldia',
            name='presencia_citricos',
            field=models.CharField(default='Ninguna', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='inventarioalcaldia',
            constraint=models.UniqueConstraint(fields=('tipo_residuo', 'presencia_citricos'), name='inventario_tipo_citricos_unico'),
        ),
    ]
