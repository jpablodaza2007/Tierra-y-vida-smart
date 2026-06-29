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
    Usuario,
    TIPO_RESIDUO_CHOICES,
)

class RegistroSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(write_only=True)
    tipo_usuario = serializers.CharField(write_only=True)
    ubicacion = serializers.CharField(write_only=True)
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
            ubicacion=validated_data.get('ubicacion', ''),
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
        datos.update({
            'nombre': perfil.nombre if perfil else self.user.get_full_name() or self.user.username,
            'email': self.user.email,
            'rol': perfil.tipo_usuario if perfil else None,
            'ubicacion': perfil.ubicacion if perfil else None,
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
            'ubicacion',
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
        read_only_fields = ['id_residuo', 'contribuyente_nombre', 'estado', 'motivo_rechazo']
        extra_kwargs = {
            'tipo_residuo': {'required': True, 'allow_blank': False},
            'cantidad_kg': {'required': True},
            'ubicacion': {'required': True, 'allow_blank': False},
            'dias_almacenamiento': {'required': True},
            'metodo_conservacion': {'required': True, 'allow_blank': False},
            'lista_materiales': {'required': True, 'allow_blank': False},
            'presencia_citricos': {'required': True, 'allow_blank': False},
            'presencia_plagas': {'required': True, 'allow_blank': False},
            'tamano_picado': {'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        validated_data['estado'] = 'Pendiente'
        validated_data['motivo_rechazo'] = ''
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

    def validate_dias_almacenamiento(self, value):
        if value is None:
            raise serializers.ValidationError('Los dias de almacenamiento son obligatorios.')
        if value < 0:
            raise serializers.ValidationError('Los dias de almacenamiento no pueden ser negativos.')
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
        return attrs


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id_sensor', 'tipo_sensor']
        read_only_fields = ['id_sensor']


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
    cantidad_kg = serializers.DecimalField(max_digits=10, decimal_places=2)
    ubicacion_entrega = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = GestionLogistica
        fields = [
            'id_gestion',
            'tipo_residuo',
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
        usuario = getattr(campesino, 'id_usuario', None)
        return (getattr(usuario, 'ubicacion', None) or '').strip()

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
        campesino = attrs.get('id_campesino') or getattr(self.instance, 'id_campesino', None)
        ubicacion_entrega = (attrs.get('ubicacion_entrega') or '').strip()

        if not ubicacion_entrega and campesino and campesino.id_usuario:
            ubicacion_entrega = (campesino.id_usuario.ubicacion or '').strip()

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
