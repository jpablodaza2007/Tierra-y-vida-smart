from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Campesino,
    Contribuyente,
    GestionLogistica,
    ResiduoOrganico,
    Sensor,
    LecturaSensor,
    SolicitudResiduo,
    SolicitudSensor,
    Usuario,
    TIPO_RESIDUO_CHOICES,
)


class LecturaSensorSerializer(serializers.ModelSerializer):
    """Valida el contenido de una lectura sin permitir elegir su dispositivo."""

    class Meta:
        model = LecturaSensor
        fields = [
            'id_lectura',
            'temperatura_ambiente',
            'humedad_ambiente',
            'humedad_suelo_porcentaje',
            'ph_suelo',
            'timestamp',
        ]
        read_only_fields = ['id_lectura', 'timestamp']

    def validate(self, attrs):
        campos = (
            'temperatura_ambiente',
            'humedad_ambiente',
            'humedad_suelo_porcentaje',
            'ph_suelo',
        )
        if not any(campo in attrs and attrs[campo] is not None for campo in campos):
            raise serializers.ValidationError('Debe enviar al menos una medición telemétrica.')
        return attrs

    def validate_humedad_ambiente(self, value):
        if value is not None and not 0 <= value <= 100:
            raise serializers.ValidationError('La humedad ambiente debe estar entre 0 y 100%.')
        return value

    def validate_humedad_suelo_porcentaje(self, value):
        if value is not None and not 0 <= value <= 100:
            raise serializers.ValidationError('La humedad del suelo debe estar entre 0 y 100%.')
        return value

    def validate_ph_suelo(self, value):
        if value is not None and not 0 <= value <= 14:
            raise serializers.ValidationError('El pH del suelo debe estar entre 0 y 14.')
        return value

class RegistroSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(write_only=True)
    tipo_usuario = serializers.CharField(write_only=True)
    ubicacion = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'nombre_completo', 'tipo_usuario', 'ubicacion']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        Usuario.objects.create(
            nombre=validated_data['nombre_completo'],
            correo=validated_data['email'],
            tipo_usuario=validated_data['tipo_usuario'],
        )
        
        return user


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get(self.username_field)
        usuario = User.objects.filter(username=username).first()

        if usuario is not None and not usuario.is_active:
            raise AuthenticationFailed(
                'Debes confirmar tu correo electrónico antes de iniciar sesión.',
                code='email_not_verified',
            )

        try:
            datos = super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed('Usuario o contraseña incorrectos.')

        perfil = Usuario.objects.filter(correo__iexact=self.user.email).first()
        rol = 'admin' if self.user.is_staff or self.user.is_superuser else (perfil.tipo_usuario if perfil else None)
        datos.update({
            'nombre': perfil.nombre if perfil else self.user.get_full_name() or self.user.username,
            'email': self.user.email,
            'rol': rol,
            'ubicacion': None,
        })
        return datos


class ResiduoOrganicoSerializer(serializers.ModelSerializer):
    contribuyente_nombre = serializers.CharField(
        source='id_contribuyente.id_usuario.nombre',
        read_only=True,
    )

    class Meta:
        model = ResiduoOrganico
        fields = [
            'id_residuo',
            'contribuyente_nombre',
            'tipo_residuo',
            'cantidad_kg',
            'peso_estimado',
            'precio_sugerido_contribuyente',
            'contraoferta_alcaldia',
            'ubicacion',
            'latitud',
            'longitud',
            'estado',
            'dias_almacenamiento',
            'metodo_conservacion',
            'lista_materiales',
            'presencia_citricos',
            'presencia_procesados',
            'ausencia_origen_animal',
            'presencia_plagas',
            'bolsa_compostable',
            'tamano_picado',
            'motivo_rechazo',
        ]
        read_only_fields = ['id_residuo', 'contribuyente_nombre', 'estado', 'motivo_rechazo', 'contraoferta_alcaldia']
        extra_kwargs = {
            'tipo_residuo': {'required': True, 'allow_blank': False},
            'cantidad_kg': {'required': True},
            'precio_sugerido_contribuyente': {'required': True},
            'latitud': {'required': True},
            'longitud': {'required': True},
            'dias_almacenamiento': {'required': True},
            'metodo_conservacion': {'required': True, 'allow_blank': False},
            'lista_materiales': {'required': True, 'allow_blank': False},
            'presencia_citricos': {'required': True, 'allow_blank': False},
            'presencia_plagas': {'required': True, 'allow_blank': False},
            'tamano_picado': {'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        validated_data['estado'] = 'PENDIENTE'
        validated_data['motivo_rechazo'] = ''
        validated_data['peso_estimado'] = validated_data.get('peso_estimado') or validated_data.get('cantidad_kg')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('estado', None)
        return super().update(instance, validated_data)

    def validate_tipo_residuo(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError('El tipo de residuo es obligatorio.')
        tipo = str(value).strip()
        valid_values = [choice[0] for choice in TIPO_RESIDUO_CHOICES]
        if tipo not in valid_values:
            raise serializers.ValidationError('Tipo de residuo inválido. Usa SECO o HUMEDO.')
        return tipo

    def validate_cantidad_kg(self, value):
        if value is None:
            raise serializers.ValidationError('La cantidad es obligatoria.')
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor que cero.')
        return value

    def validate_precio_sugerido_contribuyente(self, value):
        if value is None:
            raise serializers.ValidationError('El precio sugerido es obligatorio.')
        if value <= 0:
            raise serializers.ValidationError('El precio sugerido debe ser mayor que cero.')
        return value

    def validate_dias_almacenamiento(self, value):
        if value is None:
            raise serializers.ValidationError('Los dias de almacenamiento son obligatorios.')
        if value < 0:
            raise serializers.ValidationError('Los dias de almacenamiento no pueden ser negativos.')
        return value

    def validate_latitud(self, value):
        if value is None or not -90 <= value <= 90:
            raise serializers.ValidationError('La latitud GPS no es válida.')
        return value

    def validate_longitud(self, value):
        if value is None or not -180 <= value <= 180:
            raise serializers.ValidationError('La longitud GPS no es válida.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('presencia_procesados'):
            raise serializers.ValidationError({
                'presencia_procesados': 'Debes confirmar que el residuo esta libre de sal, aceite, aderezos o comida cocinada.'
            })
        if not attrs.get('ausencia_origen_animal'):
            raise serializers.ValidationError({
                'ausencia_origen_animal': 'Debes confirmar que el residuo esta libre de carnes, lacteos o grasas.'
            })
        if attrs.get('latitud') is not None and attrs.get('longitud') is not None:
            attrs['ubicacion'] = f"Lat: {attrs['latitud']}, Lon: {attrs['longitud']}"
        return attrs


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id_sensor', 'tipo_sensor', 'id_solicitud_sensor']
        read_only_fields = ['id_sensor', 'tipo_sensor', 'id_solicitud_sensor']


class RegistroAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id_usuario', read_only=True)
    estado = serializers.SerializerMethodField()
    comprobante_url = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    ultima_ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'nombre',
            'correo',
            'tipo_usuario',
            'ultima_ubicacion',
            'estado',
            'comprobante_url',
        ]

    def get_ultima_ubicacion(self, obj):
        campesino = getattr(obj, 'campesino', None)
        if campesino is None:
            campesino = Campesino.objects.filter(id_usuario=obj).first()
        if campesino is None:
            return None

        ultima_solicitud = (
            SolicitudResiduo.objects
            .filter(id_campesino=campesino)
            .order_by('-fecha_solicitud', '-id_solicitud_residuo')
            .first()
        )
        if ultima_solicitud is None:
            return None
        return (ultima_solicitud.ubicacion or '').strip() or None

    def get_estado(self, obj):
        estados = {
            'pendiente_aprobacion': 'PENDIENTE',
            'PENDIENTE': 'PENDIENTE',
            'aprobado': 'ACEPTADO',
            'ACEPTADO': 'ACEPTADO',
            'rechazado': 'RECHAZADO',
            'RECHAZADO': 'RECHAZADO',
        }
        return estados.get(obj.estado_cuenta, obj.estado_cuenta or 'PENDIENTE')

    def get_comprobante_url(self, obj):
        if not obj.comprobante_registro:
            return ''
        request = self.context.get('request')
        url = obj.comprobante_registro.url
        return request.build_absolute_uri(url) if request else url

    def get_username(self, obj):
        user = obj.auth_user if hasattr(obj, 'auth_user') else None
        return user.username if user else ''


class SolicitudSensorAdminSerializer(serializers.ModelSerializer):
    campesino_nombre = serializers.CharField(source='id_campesino.id_usuario.nombre', read_only=True)
    campesino_correo = serializers.CharField(source='id_campesino.id_usuario.correo', read_only=True)
    ultima_ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudSensor
        fields = [
            'id_solicitud_sensor',
            'campesino_nombre',
            'campesino_correo',
            'ultima_ubicacion',
            'tipo_sensor',
            'fecha_entrega_deseada',
            'motivo_rechazo',
            'estado',
            'fecha_solicitud',
        ]

    def get_ultima_ubicacion(self, obj):
        campesino = getattr(obj, 'id_campesino', None)
        if campesino is None:
            return None
        ultima_solicitud = (
            SolicitudResiduo.objects
            .filter(id_campesino=campesino)
            .order_by('-fecha_solicitud', '-id_solicitud_residuo')
            .first()
        )
        if ultima_solicitud is None:
            return None
        return (ultima_solicitud.ubicacion or '').strip() or None


class GestionLogisticaSerializer(serializers.ModelSerializer):
    campesino_id = serializers.PrimaryKeyRelatedField(
        source='id_campesino',
        queryset=Campesino.objects.all(),
    )
    campesino_nombre = serializers.CharField(
        source='id_campesino.id_usuario.nombre',
        read_only=True,
    )
    ubicacion = serializers.SerializerMethodField()
    tipo_residuo = serializers.ChoiceField(choices=TIPO_RESIDUO_CHOICES)
    presencia_citricos = serializers.ChoiceField(
        choices=['Ninguna', 'Baja', 'Media', 'Alta'],
        required=False,
    )
    cantidad_kg = serializers.DecimalField(max_digits=10, decimal_places=2)
    ubicacion_entrega = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = GestionLogistica
        fields = [
            'id_gestion',
            'tipo_residuo',
            'presencia_citricos',
            'cantidad_kg',
            'fecha_asignacion',
            'campesino_id',
            'campesino_nombre',
            'ubicacion_entrega',
            'ubicacion',
        ]
        read_only_fields = ['id_gestion', 'ubicacion']

    def obtener_ubicacion_campesino(self, obj):
        campesino = getattr(obj, 'id_campesino', None)
        if campesino is None:
            return ''
        ultima_solicitud = (
            SolicitudResiduo.objects
            .filter(id_campesino=campesino)
            .order_by('-fecha_solicitud', '-id_solicitud_residuo')
            .first()
        )
        return (getattr(ultima_solicitud, 'ubicacion', None) or '').strip()

    def get_ubicacion(self, obj):
        return (obj.ubicacion_entrega or self.obtener_ubicacion_campesino(obj) or '').strip()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        ubicacion = (data.get('ubicacion_entrega') or data.get('ubicacion') or self.obtener_ubicacion_campesino(instance) or '').strip()
        data['ubicacion_entrega'] = ubicacion
        data['ubicacion'] = ubicacion
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tipo_residuo = attrs.get('tipo_residuo') or getattr(self.instance, 'tipo_residuo', None)
        presencia_citricos = attrs.get('presencia_citricos') or getattr(self.instance, 'presencia_citricos', None)
        if tipo_residuo == 'HUMEDO' and presencia_citricos not in {'Ninguna', 'Baja', 'Media', 'Alta'}:
            raise serializers.ValidationError({'presencia_citricos': 'Selecciona una categoría de cítricos válida.'})
        attrs['presencia_citricos'] = presencia_citricos if tipo_residuo == 'HUMEDO' else 'Ninguna'

        campesino = attrs.get('id_campesino') or getattr(self.instance, 'id_campesino', None)
        ubicacion_entrega = (attrs.get('ubicacion_entrega') or '').strip()

        if not ubicacion_entrega and campesino:
            ultima_solicitud = (
                SolicitudResiduo.objects
                .filter(id_campesino=campesino)
                .order_by('-fecha_solicitud', '-id_solicitud_residuo')
                .first()
            )
            ubicacion_entrega = (getattr(ultima_solicitud, 'ubicacion', None) or '').strip()

        if not ubicacion_entrega:
            raise serializers.ValidationError({
                'ubicacion_entrega': 'La ubicación de entrega es obligatoria y debe venir del campesino seleccionado.'
            })

        attrs['ubicacion_entrega'] = ubicacion_entrega
        return attrs

    def validate_tipo_residuo(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError('El tipo de residuo es obligatorio.')
        return str(value).strip()

    def validate_cantidad_kg(self, value):
        if value is None:
            raise serializers.ValidationError('La cantidad es obligatoria.')
        if float(value) <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor que cero.')
        return value

    def validate_fecha_asignacion(self, value):
        if value is None:
            raise serializers.ValidationError('La fecha de asignación es obligatoria.')

        fecha_hoy = timezone.now().date()
        fecha_asignacion = value.date() if hasattr(value, 'date') else value

        if fecha_asignacion < fecha_hoy:
            raise serializers.ValidationError(
                'La alcaldía no puede gestionar asignaciones de días anteriores. Solo se permiten fechas desde el día de hoy en adelante.'
            )
        return value
