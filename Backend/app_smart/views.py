import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.utils.http import urlencode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from .models import (
    Campesino,
    Contribuyente,
    GestionLogistica,
    ResiduoOrganico,
    Sensor,
    Usuario,
)
from .serializers import (
    GestionLogisticaSerializer,
    LoginSerializer,
    ResiduoOrganicoSerializer,
    SensorSerializer,
)


VERIFICACION_EMAIL_SALT = 'app_smart.verificacion_email'


def normalizar_rol(rol):
    return (rol or '').strip().lower().replace('í', 'i')


def obtener_perfil(user):
    return Usuario.objects.filter(correo__iexact=user.email).first()


def crear_perfil_rol(perfil):
    rol = normalizar_rol(perfil.tipo_usuario)
    if rol == 'campesino':
        Campesino.objects.get_or_create(id_usuario=perfil)
    elif rol == 'contribuyente':
        Contribuyente.objects.get_or_create(id_usuario=perfil)


def crear_token_verificacion(usuario):
    return signing.dumps(
        {'user_id': usuario.pk, 'email': usuario.email},
        salt=VERIFICACION_EMAIL_SALT,
        compress=True,
    )


def enviar_correo_verificacion(usuario):
    token = crear_token_verificacion(usuario)
    url = (
        f'{settings.FRONTEND_URL}/activar-cuenta?'
        f'{urlencode({"token": token})}'
    )

    send_mail(
        subject='Confirma tu cuenta de Tierra y Vida Smart',
        message=(
            f'Hola {usuario.first_name or usuario.username},\n\n'
            'Confirma tu correo electrónico abriendo este enlace:\n'
            f'{url}\n\n'
            'El enlace vence en 24 horas. Si no creaste esta cuenta, '
            'puedes ignorar este mensaje.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=False,
    )
    return url


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class RegistroUsuarioView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        nombre_completo = request.data.get('nombre_completo')
        tipo_rol = request.data.get('tipo_rol')

        campos_faltantes = []
        if not username:
            campos_faltantes.append('usuario')
        if not email:
            campos_faltantes.append('correo')
        if not password:
            campos_faltantes.append('contraseña')
        if not nombre_completo:
            campos_faltantes.append('nombre completo')
        if not tipo_rol:
            campos_faltantes.append('tipo de rol')

        if campos_faltantes:
            return Response(
                {"error": f"Faltan campos obligatorios: {', '.join(campos_faltantes)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Ingresa un correo electrónico válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 6:
            return Response(
                {"error": "La contraseña debe tener al menos 6 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not any(c.isupper() for c in password):
            return Response(
                {"error": "La contraseña debe contener al menos una letra mayúscula."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tipo_rol_normalizado = normalizar_rol(tipo_rol)
        if tipo_rol_normalizado == 'campesino':
            tipo_rol = 'Campesino'
        elif tipo_rol_normalizado == 'contribuyente':
            tipo_rol = 'Contribuyente'
        elif tipo_rol_normalizado in ('alcaldia', 'alcaldía'):
            tipo_rol = 'Alcaldia'
        else:
            return Response(
                {"error": "Tipo de rol inválido. Usa Campesino, Contribuyente o Alcaldía."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "El nombre de usuario ya existe."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "Ya existe una cuenta registrada con este correo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                usuario_auth = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=(nombre_completo or '')[:150],
                    is_active=False,
                )

                nuevo_usuario = Usuario.objects.create(
                    nombre=nombre_completo,
                    correo=email,
                    tipo_usuario=tipo_rol
                )
                crear_perfil_rol(nuevo_usuario)

                try:
                    activacion_url = enviar_correo_verificacion(usuario_auth)
                except Exception as e:
                    logging.exception('Error al enviar correo de verificación')
                    raise

            respuesta = {
                "mensaje": (
                    "Registro completado. Revisa tu correo para activar la cuenta."
                ),
                "usuario_id": nuevo_usuario.id_usuario
            }
            if settings.DEBUG and settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
                respuesta['activacion_url'] = activacion_url

            return Response(respuesta, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Hubo un error en el servidor: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActivarCuentaView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        token = request.query_params.get('token')

        if not token:
            return Response(
                {'error': 'No se recibió el token de activación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            datos = signing.loads(
                token,
                salt=VERIFICACION_EMAIL_SALT,
                max_age=settings.EMAIL_VERIFICATION_MAX_AGE,
            )
        except signing.SignatureExpired:
            return Response(
                {'error': 'El enlace de activación ha vencido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {'error': 'El enlace de activación no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = User.objects.filter(
            pk=datos.get('user_id'),
            email__iexact=datos.get('email', ''),
        ).first()

        if usuario is None:
            return Response(
                {'error': 'No se encontró la cuenta asociada al enlace.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not usuario.is_active:
            usuario.is_active = True
            usuario.save(update_fields=['is_active'])

        return Response({'mensaje': 'Tu cuenta fue activada correctamente.'})


class GoogleLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response(
                {'error': 'No se recibió el token de Google.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            datos_google = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response(
                {'error': 'El token de Google no es válido o ha expirado.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = datos_google.get('email')
        nombre = datos_google.get('name') or email

        if not email or not datos_google.get('email_verified'):
            return Response(
                {'error': 'Google no proporcionó un correo electrónico verificado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            usuario_auth = User.objects.filter(email__iexact=email).first()

            if usuario_auth is None:
                username_base = email.split('@', 1)[0][:140] or 'usuario'
                username = username_base
                consecutivo = 1

                while User.objects.filter(username=username).exists():
                    sufijo = str(consecutivo)
                    username = f'{username_base[:150 - len(sufijo)]}{sufijo}'
                    consecutivo += 1

                usuario_auth = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=nombre[:150],
                )
                usuario_auth.set_unusable_password()
                usuario_auth.save(update_fields=['password'])
            elif not usuario_auth.is_active:
                usuario_auth.is_active = True
                usuario_auth.save(update_fields=['is_active'])

            perfil, _ = Usuario.objects.get_or_create(
                correo=email,
                defaults={
                    'nombre': nombre[:100],
                    'tipo_usuario': 'Contribuyente',
                },
            )
            crear_perfil_rol(perfil)

        refresh = RefreshToken.for_user(usuario_auth)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'nombre': nombre,
            'email': email,
            'rol': perfil.tipo_usuario,
        })


class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None:
            return Response(
                {'error': 'No se encontró el perfil del usuario.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'nombre': perfil.nombre,
            'email': perfil.correo,
            'rol': perfil.tipo_usuario,
        })


class RolQuerysetMixin:
    permission_classes = [IsAuthenticated]
    rol_requerido = ''

    def perfil_actual(self):
        perfil = obtener_perfil(self.request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != self.rol_requerido:
            self.permission_denied(
                self.request,
                message='No tienes permiso para realizar esta acción.',
            )
        return perfil


class ResiduoListCreateView(RolQuerysetMixin, ListCreateAPIView):
    serializer_class = ResiduoOrganicoSerializer
    rol_requerido = 'contribuyente'

    def get_queryset(self):
        perfil = self.perfil_actual()
        contribuyente, _ = Contribuyente.objects.get_or_create(id_usuario=perfil)
        return ResiduoOrganico.objects.filter(
            id_contribuyente=contribuyente,
        ).order_by('-id_residuo')

    def perform_create(self, serializer):
        perfil = self.perfil_actual()
        contribuyente, _ = Contribuyente.objects.get_or_create(id_usuario=perfil)
        serializer.save(id_contribuyente=contribuyente, estado='Pendiente')


class ResiduoDetailView(RolQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ResiduoOrganicoSerializer
    rol_requerido = 'contribuyente'
    lookup_field = 'id_residuo'

    def get_queryset(self):
        perfil = self.perfil_actual()
        contribuyente, _ = Contribuyente.objects.get_or_create(id_usuario=perfil)
        return ResiduoOrganico.objects.filter(id_contribuyente=contribuyente)


class SensorListCreateView(RolQuerysetMixin, ListCreateAPIView):
    serializer_class = SensorSerializer
    rol_requerido = 'campesino'

    def get_queryset(self):
        perfil = self.perfil_actual()
        campesino, _ = Campesino.objects.get_or_create(id_usuario=perfil)
        return Sensor.objects.filter(id_campesino=campesino).order_by('-id_sensor')

    def perform_create(self, serializer):
        perfil = self.perfil_actual()
        campesino, _ = Campesino.objects.get_or_create(id_usuario=perfil)
        serializer.save(id_campesino=campesino)


class SensorDetailView(RolQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = SensorSerializer
    rol_requerido = 'campesino'
    lookup_field = 'id_sensor'

    def get_queryset(self):
        perfil = self.perfil_actual()
        campesino, _ = Campesino.objects.get_or_create(id_usuario=perfil)
        return Sensor.objects.filter(id_campesino=campesino)


class GestionListCreateView(RolQuerysetMixin, ListCreateAPIView):
    serializer_class = GestionLogisticaSerializer
    rol_requerido = 'alcaldia'

    def get_queryset(self):
        self.perfil_actual()
        return GestionLogistica.objects.select_related(
            'id_residuo',
            'id_campesino__id_usuario',
        ).order_by('-fecha_asignacion', '-id_gestion')

    def perform_create(self, serializer):
        perfil = self.perfil_actual()
        gestion = serializer.save(id_usuario_alcaldia=perfil)
        if gestion.id_residuo:
            gestion.id_residuo.estado = 'Asignado'
            gestion.id_residuo.save(update_fields=['estado'])


class GestionDetailView(RolQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = GestionLogisticaSerializer
    rol_requerido = 'alcaldia'
    lookup_field = 'id_gestion'

    def get_queryset(self):
        self.perfil_actual()
        return GestionLogistica.objects.select_related(
            'id_residuo',
            'id_campesino__id_usuario',
        )

    def perform_update(self, serializer):
        gestion_anterior = self.get_object()
        residuo_anterior = gestion_anterior.id_residuo
        gestion = serializer.save(id_usuario_alcaldia=self.perfil_actual())

        if residuo_anterior and residuo_anterior != gestion.id_residuo:
            residuo_anterior.estado = 'Pendiente'
            residuo_anterior.save(update_fields=['estado'])
        if gestion.id_residuo:
            gestion.id_residuo.estado = 'Asignado'
            gestion.id_residuo.save(update_fields=['estado'])

    def perform_destroy(self, instance):
        residuo = instance.id_residuo
        instance.delete()
        if residuo:
            residuo.estado = 'Pendiente'
            residuo.save(update_fields=['estado'])


class OpcionesLogisticaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            return Response(
                {'error': 'No tienes permiso para consultar estas opciones.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        residuos = ResiduoOrganico.objects.filter(
            estado__in=['Pendiente', 'Asignado'],
        ).values('id_residuo', 'tipo_residuo', 'cantidad_kg', 'estado')
        campesinos = Campesino.objects.select_related('id_usuario').values(
            'id_campesino',
            'id_usuario__nombre',
        )
        return Response({
            'residuos': list(residuos),
            'campesinos': [
                {
                    'id_campesino': item['id_campesino'],
                    'nombre': item['id_usuario__nombre'],
                }
                for item in campesinos
            ],
        })
