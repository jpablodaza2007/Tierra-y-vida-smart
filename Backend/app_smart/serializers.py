from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import (
    Campesino,
    Contribuyente,
    GestionLogistica,
    ResiduoOrganico,
    Sensor,
    Usuario,
)

class RegistroSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(write_only=True)
    tipo_usuario = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'nombre_completo', 'tipo_usuario']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        Usuario.objects.create(
            nombre=validated_data['nombre_completo'],
            correo=validated_data['email'],
            tipo_usuario=validated_data['tipo_usuario']
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
        })
        return datos


class ResiduoOrganicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResiduoOrganico
        fields = ['id_residuo', 'tipo_residuo', 'cantidad_kg', 'estado']
        read_only_fields = ['id_residuo']
        extra_kwargs = {
            'tipo_residuo': {'required': True, 'allow_blank': False},
            'cantidad_kg': {'required': True},
        }

    def create(self, validated_data):
        validated_data['estado'] = 'Pendiente'
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('estado', None)
        return super().update(instance, validated_data)

    def validate_tipo_residuo(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError('El tipo de residuo es obligatorio.')
        return str(value).strip()

    def validate_cantidad_kg(self, value):
        if value is None:
            raise serializers.ValidationError('La cantidad es obligatoria.')
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor que cero.')
        return value


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id_sensor', 'tipo_sensor']
        read_only_fields = ['id_sensor']


class GestionLogisticaSerializer(serializers.ModelSerializer):
    residuo = ResiduoOrganicoSerializer(source='id_residuo', read_only=True)
    campesino_id = serializers.IntegerField(
        source='id_campesino_id',
        read_only=True,
    )
    campesino_nombre = serializers.CharField(
        source='id_campesino.id_usuario.nombre',
        read_only=True,
    )
    id_residuo_id = serializers.PrimaryKeyRelatedField(
        source='id_residuo',
        queryset=ResiduoOrganico.objects.all(),
        write_only=True,
    )
    id_campesino_id = serializers.PrimaryKeyRelatedField(
        source='id_campesino',
        queryset=Campesino.objects.all(),
        write_only=True,
    )

    class Meta:
        model = GestionLogistica
        fields = [
            'id_gestion',
            'id_residuo_id',
            'id_campesino_id',
            'fecha_asignacion',
            'residuo',
            'campesino_id',
            'campesino_nombre',
        ]
        read_only_fields = ['id_gestion']
