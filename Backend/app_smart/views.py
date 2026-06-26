import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db import DatabaseError
from django.utils.http import urlencode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
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
    SolicitudResiduo,
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


def enviar_correo_verificacion(usuario, *, rol=None, correo_solicitante=None, requiere_aprobacion=False, comprobante_url=None, destinatario=None):
    token = crear_token_verificacion(usuario)
    url = (
        f'{settings.FRONTEND_URL}/activar-cuenta?'
        f'{urlencode({"token": token})}'
    )

    destinatario = destinatario or (settings.ADMIN_NOTIFICATION_EMAIL or settings.DEFAULT_FROM_EMAIL or usuario.email)

    if requiere_aprobacion:
        mensaje = (
            f'Hola {settings.ADMIN_NOTIFICATION_NAME or "Administrador"},\n\n'
            'Se recibió una solicitud de registro para tu plataforma.\n\n'
            f'Correo del solicitante: {correo_solicitante or usuario.email}\n'
            f'Rol solicitado: {rol or "No especificado"}\n'
            f'Estado de la cuenta: pendiente de aprobación\n'
            f'Comprobante adjunto: {comprobante_url or "No disponible"}\n\n'
            'Puedes revisar la solicitud y decidir si apruebas o rechazas el acceso.\n\n'
            'Para activar la cuenta una vez aprobada, usa este enlace:\n'
            f'{url}\n\n'
            'El enlace vence en 24 horas. Si no creaste esta cuenta, '
            'puedes ignorar este mensaje.'
        )
        asunto = 'Solicitud de registro pendiente de aprobación - Tierra y Vida Smart'
    else:
        mensaje = (
            f'Hola {usuario.first_name or usuario.username},\n\n'
            'Confirma tu correo electrónico abriendo este enlace:\n'
            f'{url}\n\n'
            'El enlace vence en 24 horas. Si no creaste esta cuenta, '
            'puedes ignorar este mensaje.'
        )
        asunto = 'Confirma tu cuenta de Tierra y Vida Smart'
        destinatario = usuario.email

    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        fail_silently=False,
    )
    return url


def enviar_correo_aprobacion(usuario, *, nombre_usuario=None):
    destinatario = getattr(usuario, 'email', None) or None
    if not destinatario:
        raise ValueError('No existe un correo electrónico para enviar la notificación.')

    mensaje = (
        f'Hola {nombre_usuario or usuario.first_name or usuario.username},\n\n'
        'Tu cuenta en Tierra y Vida Smart ha sido verificada y habilitada con éxito.\n'
        'Ya puedes iniciar sesión y acceder a tu panel.\n\n'
        'Gracias por formar parte de nuestra plataforma.'
    )
    asunto = 'Cuenta verificada y habilitada - Tierra y Vida Smart'

    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        fail_silently=False,
    )
    return True


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class RegistroUsuarioView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        nombre_completo = request.data.get('nombre_completo')
        tipo_rol = request.data.get('tipo_rol')
        comprobante = request.FILES.get('comprobante_registro')

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

        requiere_comprobante = tipo_rol_normalizado in {'contribuyente', 'alcaldia', 'alcaldía'}
        if requiere_comprobante and not comprobante:
            return Response(
                {"error": "Este rol requiere adjuntar un comprobante de registro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if comprobante and not getattr(comprobante, 'name', '').lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            return Response(
                {"error": "El comprobante debe ser un archivo PDF o imagen."},
                status=status.HTTP_400_BAD_REQUEST,
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

                estado_cuenta = 'pendiente_aprobacion' if requiere_comprobante else 'pendiente_activacion'
                nuevo_usuario = Usuario.objects.create(
                    nombre=nombre_completo,
                    correo=email,
                    tipo_usuario=tipo_rol,
                    comprobante_registro=comprobante,
                    estado_cuenta=estado_cuenta,
                )
                crear_perfil_rol(nuevo_usuario)

                try:
                    comprobante_url = None
                    if comprobante:
                        comprobante_url = f"{request.build_absolute_uri('/')}{nuevo_usuario.comprobante_registro.url}" if nuevo_usuario.comprobante_registro else None

                    destinatario_correo = (
                        settings.ADMIN_NOTIFICATION_EMAIL
                        if requiere_comprobante
                        else email
                    )

                    activacion_url = enviar_correo_verificacion(
                        usuario_auth,
                        rol=tipo_rol,
                        correo_solicitante=email,
                        requiere_aprobacion=requiere_comprobante,
                        comprobante_url=comprobante_url,
                        destinatario=destinatario_correo,
                    )
                except Exception as e:
                    logging.exception('Error al enviar correo de verificación')
                    raise

            respuesta = {
                "mensaje": (
                    "Registro completado. Tu cuenta queda pendiente de aprobación."
                    if requiere_comprobante else
                    "Registro completado. Revisa tu correo para activar la cuenta."
                ),
                "usuario_id": nuevo_usuario.id_usuario,
                "estado_cuenta": estado_cuenta,
            }

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

        perfil = Usuario.objects.filter(correo__iexact=usuario.email).first()

        if usuario.is_active and perfil and perfil.estado_cuenta == 'aprobado':
            return Response({'mensaje': 'Tu cuenta fue activada correctamente.'})

        with transaction.atomic():
            if not usuario.is_active:
                usuario.is_active = True
                usuario.save(update_fields=['is_active'])

            if perfil is not None:
                perfil.estado_cuenta = 'aprobado'
                perfil.save(update_fields=['estado_cuenta'])

            try:
                enviar_correo_aprobacion(
                    usuario,
                    nombre_usuario=perfil.nombre if perfil else (usuario.first_name or usuario.username),
                )
            except Exception as exc:
                logging.exception('Error al enviar correo de activación')
                transaction.set_rollback(True)
                return Response(
                    {'error': 'No se pudo enviar el correo de activación. La cuenta no fue habilitada.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response({'mensaje': 'Tu cuenta fue activada correctamente.'})


<<<<<<< HEAD
class AprobarCuentaView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        usuario_id = request.data.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'Debe indicar el usuario a aprobar.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario_auth = User.objects.filter(pk=usuario_id).first()
        if usuario_auth is None:
            return Response({'error': 'No se encontró el usuario.'}, status=status.HTTP_404_NOT_FOUND)

        perfil = obtener_perfil(usuario_auth)
        if perfil is None:
            return Response({'error': 'No se encontró el perfil del usuario.'}, status=status.HTTP_404_NOT_FOUND)

        usuario_auth.is_active = True
        usuario_auth.save(update_fields=['is_active'])
        perfil.estado_cuenta = 'aprobado'
        perfil.save(update_fields=['estado_cuenta'])

        try:
            send_mail(
                subject='Cuenta aprobada - Tierra y Vida Smart',
                message=(
                    f'Hola {perfil.nombre},\n\n'
                    'Tu cuenta ha sido aprobada por el administrador. '
                    'Ya puedes iniciar sesión en la plataforma.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario_auth.email],
                fail_silently=False,
            )
        except Exception:
            logging.exception('Error al enviar correo de aprobación')

        return Response({'mensaje': 'Cuenta aprobada correctamente.'})
=======
class AprobarUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_usuario):
        return self._aprobar_usuario(request, id_usuario)

    def patch(self, request, id_usuario):
        return self._aprobar_usuario(request, id_usuario)

    def _aprobar_usuario(self, request, id_usuario):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Solo el administrador puede aprobar cuentas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            usuario_auth = User.objects.get(pk=id_usuario)
            perfil = Usuario.objects.filter(correo__iexact=usuario_auth.email).first()
        except User.DoesNotExist:
            return Response(
                {'error': 'No se encontró el usuario solicitado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if perfil is None:
            return Response(
                {'error': 'No se encontró el perfil del usuario solicitado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if usuario_auth.is_active and perfil.estado_cuenta == 'aprobado':
            return Response(
                {'mensaje': 'La cuenta ya estaba aprobada.'},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            usuario_auth.is_active = True
            usuario_auth.save(update_fields=['is_active'])
            perfil.estado_cuenta = 'aprobado'
            perfil.save(update_fields=['estado_cuenta'])

            try:
                enviar_correo_aprobacion(usuario_auth, nombre_usuario=perfil.nombre)
            except Exception as exc:
                logging.exception('Error al enviar correo de aprobación')
                transaction.set_rollback(True)
                return Response(
                    {'error': 'No se pudo enviar el correo de aprobación. La cuenta no fue habilitada.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {'mensaje': 'Cuenta aprobada y habilitada correctamente.'},
            status=status.HTTP_200_OK,
        )
>>>>>>> 159b07744d0ceed1632d39f540113bd6d24f84b9


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

        usuario_auth = User.objects.filter(email__iexact=email).first()
        perfil = Usuario.objects.filter(correo__iexact=email).first()

        if usuario_auth is None or perfil is None:
            return Response(
                {'error': 'El correo de Google no está registrado. Debe registrarse formalmente primero.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not usuario_auth.is_active:
            return Response(
                {'error': 'La cuenta aún no está activa. Debe esperar aprobación o activar su correo.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if perfil.estado_cuenta == 'pendiente_aprobacion':
            return Response(
                {'error': 'La cuenta está pendiente de aprobación por parte del administrador.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(usuario_auth)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'nombre': nombre,
            'email': email,
            'rol': perfil.tipo_usuario,
        })


class SolicitudSensorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tipo_sensor = request.data.get('tipo_sensor')
        perfil = obtener_perfil(request.user)

        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden solicitar sensores.'}, status=status.HTTP_403_FORBIDDEN)
        if not tipo_sensor:
            return Response({'error': 'Debe indicar el tipo de sensor.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_mail(
                subject='Solicitud de sensor - Tierra y Vida Smart',
                message=(
                    f'Hola Administrador,\n\n'
                    f'El campesino {perfil.nombre} solicitó un sensor del tipo {tipo_sensor}.\n'
                    f'Correo del campesino: {request.user.email}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL or settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
        except Exception:
            logging.exception('Error al enviar correo de solicitud de sensor')

        return Response({'mensaje': 'Solicitud enviada correctamente.'}, status=status.HTTP_201_CREATED)


class SolicitudResiduoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            return Response({'error': 'Solo la alcaldía puede ver las solicitudes de residuos.'}, status=status.HTTP_403_FORBIDDEN)

        solicitudes = (
            SolicitudResiduo.objects.select_related('id_campesino', 'id_residuo')
            .filter(estado='pendiente')
            .order_by('-fecha_solicitud')
        )

        datos = []
        for solicitud in solicitudes:
            campesino_nombre = ''
            if solicitud.id_campesino and solicitud.id_campesino.id_usuario:
                campesino_nombre = solicitud.id_campesino.id_usuario.nombre

            datos.append({
                'id_solicitud_residuo': solicitud.id_solicitud_residuo,
                'id_campesino': solicitud.id_campesino_id,
                'campesino_nombre': campesino_nombre,
                'id_residuo': solicitud.id_residuo_id,
                'tipo_residuo': solicitud.id_residuo.tipo_residuo if solicitud.id_residuo else None,
                'cantidad_kg': solicitud.id_residuo.cantidad_kg if solicitud.id_residuo else None,
                'estado': solicitud.estado,
                'fecha_solicitud': solicitud.fecha_solicitud,
            })

        return Response(datos, status=status.HTTP_200_OK)

    def post(self, request):
        id_residuo = request.data.get('id_residuo')
        perfil = obtener_perfil(request.user)

        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden solicitar residuos.'}, status=status.HTTP_403_FORBIDDEN)
        if not id_residuo:
            return Response({'error': 'Debe seleccionar un residuo aprobado.'}, status=status.HTTP_400_BAD_REQUEST)

        residuo = ResiduoOrganico.objects.filter(pk=id_residuo, estado='Disponible').first()
        if residuo is None:
            return Response({'error': 'No se encontró un residuo aprobado para solicitar.'}, status=status.HTTP_404_NOT_FOUND)

        campesino = Campesino.objects.filter(id_usuario=perfil).first()
        if campesino is None:
            return Response({'error': 'No se encontró el perfil de campesino asociado.'}, status=status.HTTP_404_NOT_FOUND)

        SolicitudResiduo.objects.create(id_campesino=campesino, id_residuo=residuo, estado='pendiente')

        return Response({'mensaje': 'Solicitud registrada para la alcaldía.'}, status=status.HTTP_201_CREATED)


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


class ResiduoDisponibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'No tienes permiso para consultar estos residuos.'}, status=status.HTTP_403_FORBIDDEN)

        residuos = ResiduoOrganico.objects.filter(estado='Disponible').values('id_residuo', 'tipo_residuo', 'cantidad_kg', 'estado')
        return Response(list(residuos))


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


class MisAsignacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden ver sus asignaciones.'}, status=status.HTTP_403_FORBIDDEN)

        campesino = Campesino.objects.filter(id_usuario=perfil).first()
        if campesino is None:
            return Response({'error': 'No se encontró el perfil de campesino asociado.'}, status=status.HTTP_404_NOT_FOUND)

        asignaciones = (
            GestionLogistica.objects.filter(id_campesino=campesino)
            .select_related('id_residuo')
            .order_by('-fecha_asignacion', '-id_gestion')
        )

        datos = []
        for asignacion in asignaciones:
            datos.append({
                'id_gestion': asignacion.id_gestion,
                'tipo_residuo': asignacion.id_residuo.tipo_residuo if asignacion.id_residuo else None,
                'cantidad_kg': asignacion.id_residuo.cantidad_kg if asignacion.id_residuo else None,
                'fecha_asignacion': asignacion.fecha_asignacion,
            })

        return Response(datos, status=status.HTTP_200_OK)


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
