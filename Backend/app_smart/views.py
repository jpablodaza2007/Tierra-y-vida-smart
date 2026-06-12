from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Usuario 

class RegistroUsuarioView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        nombre_completo = request.data.get('nombre_completo')
        tipo_rol = request.data.get('tipo_rol')

        if not username or not password or not email:
            return Response(
                {"error": "Faltan campos obligatorios (username, password, email)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": " El nombre de usuario ya existe."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user_auth = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            
            nuevo_usuario = Usuario.objects.create(
                nombre=nombre_completo,
                correo=email,
                tipo_usuario=tipo_rol 
            )
            
            return Response({
                "mensaje": f" ¡Usuario {username} registrado exitosamente!",
                "usuario_id": nuevo_usuario.id_usuario
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Hubo un error en el servidor: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )