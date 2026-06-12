from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Usuario

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