from django.contrib import admin
from .models import DispositivoSensor, LecturaSensor


@admin.register(DispositivoSensor)
class DispositivoSensorAdmin(admin.ModelAdmin):
    list_display = ('codigo_mac', 'campesino', 'referencia_hardware', 'estado', 'fecha_vinculacion')
    list_filter = ('referencia_hardware', 'estado')
    search_fields = ('codigo_mac', 'campesino__nombre', 'campesino__correo')


@admin.register(LecturaSensor)
class LecturaSensorAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'temperatura_ambiente', 'humedad_suelo_porcentaje', 'ph_suelo', 'timestamp')
    list_filter = ('dispositivo__referencia_hardware',)
    search_fields = ('dispositivo__codigo_mac',)
    readonly_fields = ('timestamp',)
