import logging
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db import DatabaseError
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.http import urlencode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from .models import (
    Alcaldia,
    Campesino,
    Contribuyente,
    GestionLogistica,
    InventarioAlcaldia,
    ResiduoOrganico,
    Sensor,
    SolicitudResiduo,
    SolicitudSensor,
    Usuario,
)
from .serializers import (
    GestionLogisticaSerializer,
    LoginSerializer,
    RegistroAdminSerializer,
    ResiduoOrganicoSerializer,
    SensorSerializer,
    SolicitudSensorAdminSerializer,
)


VERIFICACION_EMAIL_SALT = 'app_smart.verificacion_email'


def normalizar_rol(rol):
    return (rol or '').strip().lower().replace('í', 'i')


def decimal_positivo(valor, nombre_campo):
    try:
        numero = Decimal(str(valor))
    except Exception:
        raise serializers.ValidationError({nombre_campo: ['Debe ser un valor numerico valido.']})
    if numero <= 0:
        raise serializers.ValidationError({nombre_campo: ['Debe ser mayor que cero.']})
    return numero


def obtener_perfil(user):
    return Usuario.objects.filter(correo__iexact=user.email).first()


def crear_perfil_rol(perfil):
    rol = normalizar_rol(perfil.tipo_usuario)
    if rol == 'campesino':
        Campesino.objects.get_or_create(id_usuario=perfil)
    elif rol == 'contribuyente':
        Contribuyente.objects.get_or_create(id_usuario=perfil)
    elif rol in {'alcaldia', 'alcaldía'}:
        Alcaldia.objects.get_or_create(id_usuario=perfil)


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
            'Puedes revisar la solicitud y decidir si apruebas o rechazas el acceso '
            'desde el panel de administracion.\n\n'
            'El solicitante recibira una notificacion automatica cuando registres el dictamen.'
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


def enviar_correo_dictamen(usuario, *, nombre_usuario=None, estado='ACEPTADO', contexto='cuenta'):
    destinatario = getattr(usuario, 'email', None) or None
    if not destinatario:
        raise ValueError('No existe un correo electronico para enviar la notificacion.')

    nombre = nombre_usuario or usuario.first_name or usuario.username
    if estado == 'ACEPTADO':
        asunto = 'Solicitud aprobada - Tierra y Vida Smart'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu solicitud de {contexto} fue aprobada por el administrador.\n'
            'Tu cuenta en Tierra y Vida Smart ha sido activada y ya puedes iniciar sesion.\n\n'
            'Gracias por formar parte de nuestra plataforma.'
        )
    else:
        asunto = 'Solicitud rechazada - Tierra y Vida Smart'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu solicitud de {contexto} fue rechazada tras la revision administrativa.\n'
            'Si consideras que debes corregir la documentacion, comunicate con el equipo de Tierra y Vida Smart.\n\n'
            'Gracias por tu interes en la plataforma.'
        )

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

                estado_cuenta = 'PENDIENTE' if requiere_comprobante else 'pendiente_activacion'
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

        if perfil.estado_cuenta in {'pendiente_aprobacion', 'PENDIENTE'}:
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

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden consultar sus solicitudes de sensores.'}, status=status.HTTP_403_FORBIDDEN)

        campesino = Campesino.objects.filter(id_usuario=perfil).first()
        if campesino is None:
            return Response([], status=status.HTTP_200_OK)

        solicitudes = (
            SolicitudSensor.objects
            .filter(id_campesino=campesino)
            .order_by('-fecha_solicitud', '-id_solicitud_sensor')
        )
        return Response([
            {
                'id_solicitud_sensor': solicitud.id_solicitud_sensor,
                'tipo_sensor': solicitud.tipo_sensor,
                'fecha_entrega_deseada': solicitud.fecha_entrega_deseada,
                'motivo_rechazo': solicitud.motivo_rechazo or '',
                'estado': solicitud.estado,
                'fecha_solicitud': solicitud.fecha_solicitud,
            }
            for solicitud in solicitudes
        ], status=status.HTTP_200_OK)

    def post(self, request):
        tipos_sensores = request.data.get('tipo_sensores')
        tipo_sensor = request.data.get('tipo_sensor')
        fecha_entrega_deseada = parse_date(str(request.data.get('fecha_entrega_deseada') or ''))
        perfil = obtener_perfil(request.user)

        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden solicitar sensores.'}, status=status.HTTP_403_FORBIDDEN)
        if fecha_entrega_deseada is None:
            return Response({'error': 'Debe indicar la fecha deseada de recepcion.'}, status=status.HTTP_400_BAD_REQUEST)
        if fecha_entrega_deseada < timezone.localdate():
            return Response({'error': 'La fecha deseada de recepcion no puede estar en el pasado.'}, status=status.HTTP_400_BAD_REQUEST)

        if tipos_sensores is None:
            tipos_sensores = [tipo_sensor] if tipo_sensor else []
        elif isinstance(tipos_sensores, str):
            tipos_sensores = [tipos_sensores]

        tipos_validos = {'Temperatura', 'pH', 'Humedad'}
        tipos_sensores = [str(sensor).strip() for sensor in tipos_sensores if str(sensor).strip()]
        tipos_sensores = list(dict.fromkeys(tipos_sensores))

        if not tipos_sensores:
            return Response({'error': 'Debe indicar el tipo de sensor.'}, status=status.HTTP_400_BAD_REQUEST)
        if any(sensor not in tipos_validos for sensor in tipos_sensores):
            return Response({'error': 'Tipo de sensor invalido. Usa Temperatura, pH o Humedad.'}, status=status.HTTP_400_BAD_REQUEST)

        campesino, _ = Campesino.objects.get_or_create(id_usuario=perfil)
        for sensor in tipos_sensores:
            SolicitudSensor.objects.create(
                id_campesino=campesino,
                tipo_sensor=sensor,
                fecha_entrega_deseada=fecha_entrega_deseada,
                estado='PENDIENTE',
            )

        try:
            sensores_texto = ', '.join(tipos_sensores)
            send_mail(
                subject='Solicitud de sensor - Tierra y Vida Smart',
                message=(
                    f'Hola Administrador,\n\n'
                    f'El campesino {perfil.nombre} solicito sensores del tipo {sensores_texto}.\n'
                    f'Correo del campesino: {request.user.email}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL or settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
        except Exception:
            logging.exception('Error al enviar correo de solicitud de sensor')

        return Response({
            'mensaje': 'Solicitud enviada correctamente.',
            'tipo_sensores': tipos_sensores,
            'fecha_entrega_deseada': fecha_entrega_deseada,
        }, status=status.HTTP_201_CREATED)


class SolicitudResiduoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        rol = normalizar_rol(perfil.tipo_usuario) if perfil else ''

        if rol == 'alcaldia':
            solicitudes = (
                SolicitudResiduo.objects.select_related('id_campesino__id_usuario')
                .exclude(estado__in=['RECHAZADO', 'rechazado', 'asignada'])
                .order_by('-fecha_solicitud')
            )
        elif rol == 'campesino':
            campesino = Campesino.objects.filter(id_usuario=perfil).first()
            if campesino is None:
                return Response({'error': 'No se encontro el perfil de campesino asociado.'}, status=status.HTTP_404_NOT_FOUND)
            solicitudes = (
                SolicitudResiduo.objects.select_related('id_campesino__id_usuario')
                .filter(id_campesino=campesino)
                .order_by('-fecha_solicitud')
            )
        else:
            return Response({'error': 'No tienes permiso para ver solicitudes de residuos.'}, status=status.HTTP_403_FORBIDDEN)

        datos = []
        for solicitud in solicitudes:
            campesino_nombre = ''
            if solicitud.id_campesino and solicitud.id_campesino.id_usuario:
                campesino_nombre = solicitud.id_campesino.id_usuario.nombre

            datos.append({
                'id_solicitud_residuo': solicitud.id_solicitud_residuo,
                'id_campesino': solicitud.id_campesino_id,
                'campesino_nombre': campesino_nombre,
                'tipo_residuo': solicitud.tipo_residuo,
                'cantidad_kg': solicitud.cantidad_kg,
                'cantidad_solicitada': solicitud.cantidad_solicitada,
                'precio_ofrecido_campesino': solicitud.precio_ofrecido_campesino,
                'contraoferta_alcaldia': solicitud.contraoferta_alcaldia,
                'ubicacion': solicitud.ubicacion,
                'estado': solicitud.estado,
                'fecha_solicitud': solicitud.fecha_solicitud,
            })

        return Response(datos, status=status.HTTP_200_OK)

    def post(self, request):
        tipo_residuo = request.data.get('tipo_residuo')
        cantidad_kg = request.data.get('cantidad_kg') or request.data.get('cantidad_solicitada')
        precio_ofrecido = request.data.get('precio_ofrecido_campesino')
        ubicacion = request.data.get('ubicacion')
        perfil = obtener_perfil(request.user)

        if not perfil or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo los campesinos pueden solicitar residuos.'}, status=status.HTTP_403_FORBIDDEN)
        if not tipo_residuo:
            return Response({'error': 'Debe seleccionar el tipo de residuo.'}, status=status.HTTP_400_BAD_REQUEST)
        if tipo_residuo not in {'SECO', 'HUMEDO'}:
            return Response({'error': 'Tipo de residuo inválido. Usa SECO o HUMEDO.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cantidad_kg = float(cantidad_kg)
        except (TypeError, ValueError):
            cantidad_kg = None

        if cantidad_kg is None or cantidad_kg <= 0:
            return Response({'error': 'Debes indicar una cantidad en kg mayor a cero.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            precio_ofrecido = decimal_positivo(precio_ofrecido, 'precio_ofrecido_campesino')
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        if not ubicacion or not str(ubicacion).strip():
            return Response({'error': 'La ubicación es obligatoria.'}, status=status.HTTP_400_BAD_REQUEST)

        campesino = Campesino.objects.filter(id_usuario=perfil).first()
        if campesino is None:
            return Response({'error': 'No se encontró el perfil de campesino asociado.'}, status=status.HTTP_404_NOT_FOUND)

        SolicitudResiduo.objects.create(
            id_campesino=campesino,
            tipo_residuo=tipo_residuo,
            cantidad_kg=cantidad_kg,
            cantidad_solicitada=cantidad_kg,
            precio_ofrecido_campesino=precio_ofrecido,
            ubicacion=str(ubicacion).strip(),
            estado='PENDIENTE',
        )

        return Response({'mensaje': 'Solicitud registrada para la alcaldía.'}, status=status.HTTP_201_CREATED)


def serializar_solicitud_residuo(solicitud):
    campesino_nombre = ''
    if solicitud.id_campesino and solicitud.id_campesino.id_usuario:
        campesino_nombre = solicitud.id_campesino.id_usuario.nombre

    return {
        'id_solicitud_residuo': solicitud.id_solicitud_residuo,
        'id_campesino': solicitud.id_campesino_id,
        'campesino_nombre': campesino_nombre,
        'tipo_residuo': solicitud.tipo_residuo,
        'cantidad_kg': solicitud.cantidad_kg,
        'cantidad_solicitada': solicitud.cantidad_solicitada,
        'precio_ofrecido_campesino': solicitud.precio_ofrecido_campesino,
        'contraoferta_alcaldia': solicitud.contraoferta_alcaldia,
        'ubicacion': solicitud.ubicacion,
        'estado': solicitud.estado,
        'fecha_solicitud': solicitud.fecha_solicitud,
    }


def decidir_solicitud_residuo_alcaldia(request, id_solicitud_residuo):
    perfil = obtener_perfil(request.user)
    if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
        return Response({'error': 'Solo la alcaldia puede auditar solicitudes de residuos.'}, status=status.HTTP_403_FORBIDDEN)

    decision = (request.data.get('estado') or request.data.get('decision') or '').strip().lower()
    contraoferta = request.data.get('contraoferta_alcaldia')
    if decision in {'aceptar', 'aceptado', 'aprobar', 'aprobado'}:
        estado_nuevo = 'APROBADO'
        contraoferta = None
    elif decision in {'contraoferta', 'contraoferta_alcaldia'} or contraoferta not in (None, ''):
        estado_nuevo = 'CONTRAOFERTA_ALCALDIA'
        try:
            contraoferta = decimal_positivo(contraoferta, 'contraoferta_alcaldia')
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    elif decision in {'rechazar', 'rechazado'}:
        estado_nuevo = 'RECHAZADO'
        contraoferta = None
    else:
        return Response({'error': 'La decision debe ser APROBADO, RECHAZADO o CONTRAOFERTA_ALCALDIA.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            solicitud = (
                SolicitudResiduo.objects
                .select_related('id_campesino__id_usuario')
                .select_for_update(of=('self',))
                .get(pk=id_solicitud_residuo)
            )
            if solicitud.estado not in {'PENDIENTE', 'pendiente'}:
                return Response({'error': 'Esta solicitud ya fue auditada.'}, status=status.HTTP_400_BAD_REQUEST)

            solicitud.estado = estado_nuevo
            solicitud.contraoferta_alcaldia = contraoferta
            solicitud.save(update_fields=['estado', 'contraoferta_alcaldia'])
    except SolicitudResiduo.DoesNotExist:
        return Response({'error': 'No se encontro la solicitud de residuo.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializar_solicitud_residuo(solicitud), status=status.HTTP_200_OK)


class AuditoriaSolicitudResiduoDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_solicitud_residuo):
        return self._decidir(request, id_solicitud_residuo)

    def post(self, request, id_solicitud_residuo):
        return self._decidir(request, id_solicitud_residuo)

    def _decidir(self, request, id_solicitud_residuo):
        return decidir_solicitud_residuo_alcaldia(request, id_solicitud_residuo)


class RespuestaContraofertaSolicitudResiduoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_solicitud_residuo):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'Solo el campesino puede responder esta contraoferta.'}, status=status.HTTP_403_FORBIDDEN)

        decision = (request.data.get('decision') or request.data.get('estado') or '').strip().lower()
        if decision in {'aceptar', 'aceptado', 'aceptado_por_campesino'}:
            estado_nuevo = 'ACEPTADO_POR_CAMPESINO'
        elif decision in {'rechazar', 'rechazado', 'cancelar', 'cancelado'}:
            estado_nuevo = 'RECHAZADO'
        else:
            return Response({'error': 'La decision debe ser aceptar o rechazar.'}, status=status.HTTP_400_BAD_REQUEST)

        campesino = Campesino.objects.filter(id_usuario=perfil).first()
        if campesino is None:
            return Response({'error': 'No se encontro el perfil de campesino asociado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                solicitud = (
                    SolicitudResiduo.objects
                    .select_related('id_campesino__id_usuario')
                    .select_for_update(of=('self',))
                    .get(pk=id_solicitud_residuo, id_campesino=campesino)
                )
                if solicitud.estado != 'CONTRAOFERTA_ALCALDIA':
                    return Response({'error': 'Esta solicitud no tiene una contraoferta pendiente.'}, status=status.HTTP_400_BAD_REQUEST)

                solicitud.estado = estado_nuevo
                solicitud.save(update_fields=['estado'])
        except SolicitudResiduo.DoesNotExist:
            return Response({'error': 'No se encontro la solicitud de residuo.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializar_solicitud_residuo(solicitud), status=status.HTTP_200_OK)


def normalizar_estado_dictamen(valor):
    estado = (valor or '').strip().upper()
    if estado in {'ACEPTAR', 'APROBAR', 'APROBADO'}:
        return 'ACEPTADO'
    if estado in {'RECHAZAR', 'RECHAZADO'}:
        return 'RECHAZADO'
    if estado in {'ACEPTADO', 'RECHAZADO'}:
        return estado
    return ''


class RegistroAdminViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RegistroAdminSerializer
    permission_classes = [IsAdminUser]
    rol = ''
    contexto_correo = 'registro'

    def get_queryset(self):
        return (
            Usuario.objects
            .filter(tipo_usuario__iexact=self.rol)
            .exclude(comprobante_registro='')
            .exclude(comprobante_registro__isnull=True)
            .order_by('-id_usuario')
        )

    @action(detail=True, methods=['patch'])
    def dictaminar(self, request, pk=None):
        estado = normalizar_estado_dictamen(request.data.get('estado'))
        if not estado:
            return Response({'error': 'El estado debe ser ACEPTADO o RECHAZADO.'}, status=status.HTTP_400_BAD_REQUEST)

        perfil = self.get_object()
        usuario_auth = User.objects.filter(email__iexact=perfil.correo).first()
        if usuario_auth is None:
            return Response({'error': 'No se encontro el usuario asociado al perfil.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            usuario_auth.is_active = estado == 'ACEPTADO'
            usuario_auth.save(update_fields=['is_active'])
            perfil.estado_cuenta = estado
            perfil.save(update_fields=['estado_cuenta'])

            try:
                enviar_correo_dictamen(
                    usuario_auth,
                    nombre_usuario=perfil.nombre,
                    estado=estado,
                    contexto=self.contexto_correo,
                )
            except Exception:
                logging.exception('Error al enviar correo de dictamen de registro')
                transaction.set_rollback(True)
                return Response(
                    {'error': 'No se pudo enviar el correo de notificacion. No se aplico el dictamen.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(self.get_serializer(perfil).data, status=status.HTTP_200_OK)


class ContribuyenteAdminViewSet(RegistroAdminViewSet):
    rol = 'Contribuyente'
    contexto_correo = 'registro de contribuyente'


class AlcaldiaAdminViewSet(RegistroAdminViewSet):
    rol = 'Alcaldia'
    contexto_correo = 'registro de alcaldia'


class SolicitudSensorAdminViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SolicitudSensorAdminSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            SolicitudSensor.objects
            .select_related('id_campesino__id_usuario')
            .order_by('-fecha_solicitud', '-id_solicitud_sensor')
        )

    @action(detail=True, methods=['patch'])
    def dictaminar(self, request, pk=None):
        estado = normalizar_estado_dictamen(request.data.get('estado'))
        if not estado:
            return Response({'error': 'El estado debe ser ACEPTADO o RECHAZADO.'}, status=status.HTTP_400_BAD_REQUEST)

        solicitud = self.get_object()
        if solicitud.estado != 'PENDIENTE':
            return Response({'error': 'Esta solicitud ya fue dictaminada.'}, status=status.HTTP_400_BAD_REQUEST)

        perfil = solicitud.id_campesino.id_usuario if solicitud.id_campesino else None
        usuario_auth = User.objects.filter(email__iexact=perfil.correo).first() if perfil else None
        if perfil is None or usuario_auth is None:
            return Response({'error': 'No se encontro el campesino asociado a la solicitud.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            solicitud.estado = estado
            if estado == 'RECHAZADO':
                solicitud.motivo_rechazo = (request.data.get('motivo_rechazo') or '').strip()
            else:
                solicitud.motivo_rechazo = ''
            solicitud.save(update_fields=['estado', 'motivo_rechazo'])

            if estado == 'ACEPTADO':
                Sensor.objects.create(
                    id_campesino=solicitud.id_campesino,
                    tipo_sensor=solicitud.tipo_sensor,
                )

            try:
                enviar_correo_dictamen(
                    usuario_auth,
                    nombre_usuario=perfil.nombre,
                    estado=estado,
                    contexto=f'solicitud de sensor {solicitud.tipo_sensor}',
                )
            except Exception:
                logging.exception('Error al enviar correo de dictamen de sensor')
                transaction.set_rollback(True)
                return Response(
                    {'error': 'No se pudo enviar el correo de notificacion. No se aplico el dictamen.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)


class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None:
            if request.user.is_staff or request.user.is_superuser:
                return Response({
                    'nombre': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'rol': 'admin',
                    'ubicacion': '',
                })
            return Response(
                {'error': 'No se encontró el perfil del usuario.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'nombre': perfil.nombre if perfil else request.user.get_full_name() or request.user.username,
            'email': perfil.correo,
            'rol': 'admin' if request.user.is_staff or request.user.is_superuser else perfil.tipo_usuario,
            'ubicacion': '',
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
        serializer.save(id_contribuyente=contribuyente, estado='PENDIENTE', motivo_rechazo='')


class ResiduoDisponibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'campesino':
            return Response({'error': 'No tienes permiso para consultar estos residuos.'}, status=status.HTTP_403_FORBIDDEN)

        residuos = ResiduoOrganico.objects.filter(
            estado__in=['APROBADO', 'Aceptado', 'Disponible', 'ACEPTADO_POR_CONTRIBUYENTE'],
        ).values('id_residuo', 'tipo_residuo', 'cantidad_kg', 'peso_estimado', 'estado')
        return Response(list(residuos))


class ResiduoDetailView(RolQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ResiduoOrganicoSerializer
    rol_requerido = 'contribuyente'
    lookup_field = 'id_residuo'

    def get_queryset(self):
        perfil = self.perfil_actual()
        contribuyente, _ = Contribuyente.objects.get_or_create(id_usuario=perfil)
        return ResiduoOrganico.objects.filter(id_contribuyente=contribuyente)


class AuditoriaResiduoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            return Response({'error': 'Solo la alcaldia puede auditar residuos.'}, status=status.HTTP_403_FORBIDDEN)

        residuos = (
            ResiduoOrganico.objects.select_related('id_contribuyente__id_usuario')
            .filter(estado__in=['PENDIENTE', 'Pendiente'])
            .order_by('-id_residuo')
        )
        return Response(ResiduoOrganicoSerializer(residuos, many=True).data, status=status.HTTP_200_OK)


def decidir_residuo_alcaldia(request, id_residuo):
    perfil = obtener_perfil(request.user)
    if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
        return Response({'error': 'Solo la alcaldia puede auditar residuos.'}, status=status.HTTP_403_FORBIDDEN)

    decision = (request.data.get('estado') or request.data.get('decision') or '').strip().lower()
    contraoferta = request.data.get('contraoferta_alcaldia')
    if decision in {'aceptar', 'aceptado', 'aprobar', 'aprobado'}:
        estado_nuevo = 'APROBADO'
    elif decision in {'contraoferta', 'contraoferta_alcaldia'} or contraoferta not in (None, ''):
        estado_nuevo = 'CONTRAOFERTA_ALCALDIA'
        try:
            contraoferta = decimal_positivo(contraoferta, 'contraoferta_alcaldia')
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    elif decision in {'rechazar', 'rechazado'}:
        estado_nuevo = 'RECHAZADO'
    else:
        return Response({'error': 'La decision debe ser APROBADO, RECHAZADO o CONTRAOFERTA_ALCALDIA.'}, status=status.HTTP_400_BAD_REQUEST)

    motivo_rechazo = (request.data.get('motivo_rechazo') or '').strip()
    if estado_nuevo == 'RECHAZADO' and not motivo_rechazo:
        return Response({'error': 'El motivo de rechazo es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            residuo = ResiduoOrganico.objects.select_for_update(of=('self',)).get(pk=id_residuo)

            if residuo.estado not in {'PENDIENTE', 'Pendiente'}:
                return Response({'error': 'Este residuo ya fue auditado.'}, status=status.HTTP_400_BAD_REQUEST)

            residuo.estado = estado_nuevo
            residuo.contraoferta_alcaldia = contraoferta if estado_nuevo == 'CONTRAOFERTA_ALCALDIA' else None
            residuo.motivo_rechazo = motivo_rechazo if estado_nuevo == 'RECHAZADO' else ''
            residuo.save(update_fields=['estado', 'motivo_rechazo', 'contraoferta_alcaldia'])

            if estado_nuevo == 'APROBADO':
                inventario, _ = InventarioAlcaldia.objects.select_for_update().get_or_create(tipo_residuo=residuo.tipo_residuo)
                inventario.cantidad_total_kg = Decimal(str(inventario.cantidad_total_kg)) + Decimal(str(residuo.cantidad_kg))
                inventario.save(update_fields=['cantidad_total_kg'])

    except ResiduoOrganico.DoesNotExist:
        return Response({'error': 'No se encontro el residuo solicitado.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(ResiduoOrganicoSerializer(residuo).data, status=status.HTTP_200_OK)


class AuditoriaResiduoDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_residuo):
        return self._decidir(request, id_residuo)

    def post(self, request, id_residuo):
        return self._decidir(request, id_residuo)

    def _decidir(self, request, id_residuo):
        return decidir_residuo_alcaldia(request, id_residuo)


class AuditoriaResiduoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResiduoOrganicoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id_residuo'

    def get_queryset(self):
        perfil = obtener_perfil(self.request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            self.permission_denied(self.request, message='Solo la alcaldia puede auditar residuos.')
        return (
            ResiduoOrganico.objects.select_related('id_contribuyente__id_usuario')
            .filter(estado__in=['PENDIENTE', 'Pendiente'])
            .order_by('-id_residuo')
        )

    @action(detail=True, methods=['patch'], url_path='decision')
    def decision(self, request, id_residuo=None):
        return decidir_residuo_alcaldia(request, id_residuo)


class AuditoriaSolicitudResiduoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id_solicitud_residuo'

    def get_queryset(self):
        perfil = obtener_perfil(self.request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            self.permission_denied(self.request, message='Solo la alcaldia puede auditar solicitudes de residuos.')
        return (
            SolicitudResiduo.objects.select_related('id_campesino__id_usuario')
            .exclude(estado__in=['RECHAZADO', 'rechazado', 'asignada'])
            .order_by('-fecha_solicitud')
        )

    def list(self, request, *args, **kwargs):
        return Response(
            [serializar_solicitud_residuo(solicitud) for solicitud in self.get_queryset()],
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        return Response(serializar_solicitud_residuo(self.get_object()), status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='decision')
    def decision(self, request, id_solicitud_residuo=None):
        return decidir_solicitud_residuo_alcaldia(request, id_solicitud_residuo)


class RespuestaContraofertaResiduoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_residuo):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'contribuyente':
            return Response({'error': 'Solo el contribuyente puede responder esta contraoferta.'}, status=status.HTTP_403_FORBIDDEN)

        decision = (request.data.get('decision') or request.data.get('estado') or '').strip().lower()
        if decision in {'aceptar', 'aceptado', 'aceptado_por_contribuyente'}:
            estado_nuevo = 'ACEPTADO_POR_CONTRIBUYENTE'
        elif decision in {'rechazar', 'rechazado'}:
            estado_nuevo = 'RECHAZADO'
        else:
            return Response({'error': 'La decision debe ser aceptar o rechazar.'}, status=status.HTTP_400_BAD_REQUEST)

        contribuyente = Contribuyente.objects.filter(id_usuario=perfil).first()
        if contribuyente is None:
            return Response({'error': 'No se encontro el perfil de contribuyente asociado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                residuo = (
                    ResiduoOrganico.objects
                    .select_for_update(of=('self',))
                    .get(pk=id_residuo, id_contribuyente=contribuyente)
                )

                if residuo.estado != 'CONTRAOFERTA_ALCALDIA':
                    return Response({'error': 'Este residuo no tiene una contraoferta pendiente.'}, status=status.HTTP_400_BAD_REQUEST)

                residuo.estado = estado_nuevo
                residuo.save(update_fields=['estado'])

                if estado_nuevo == 'ACEPTADO_POR_CONTRIBUYENTE':
                    inventario, _ = InventarioAlcaldia.objects.select_for_update().get_or_create(tipo_residuo=residuo.tipo_residuo)
                    inventario.cantidad_total_kg = Decimal(str(inventario.cantidad_total_kg)) + Decimal(str(residuo.cantidad_kg))
                    inventario.save(update_fields=['cantidad_total_kg'])

        except ResiduoOrganico.DoesNotExist:
            return Response({'error': 'No se encontro el residuo solicitado.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ResiduoOrganicoSerializer(residuo).data, status=status.HTTP_200_OK)


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
            GestionLogistica.objects.select_related('id_campesino__id_usuario')
            .filter(id_campesino=campesino)
            .order_by('-fecha_asignacion', '-id_gestion')
        )

        datos = []
        for asignacion in asignaciones:
            campesino_ubicacion = ''
            campesino_nombre = ''
            if asignacion.id_campesino and asignacion.id_campesino.id_usuario:
                campesino_nombre = asignacion.id_campesino.id_usuario.nombre or ''
                ultima_solicitud = (
                    SolicitudResiduo.objects
                    .filter(id_campesino=asignacion.id_campesino)
                    .order_by('-fecha_solicitud', '-id_solicitud_residuo')
                    .first()
                )
                campesino_ubicacion = (getattr(ultima_solicitud, 'ubicacion', None) or '').strip()
            ubicacion_entrega = asignacion.ubicacion_entrega or campesino_ubicacion or ''

            datos.append({
                'id_gestion': asignacion.id_gestion,
                'tipo_residuo': asignacion.tipo_residuo,
                'cantidad_kg': asignacion.cantidad_kg,
                'fecha_asignacion': asignacion.fecha_asignacion,
                'ubicacion_entrega': ubicacion_entrega,
                'ubicacion': ubicacion_entrega or campesino_ubicacion,
                'campesino': {
                    'nombre': campesino_nombre,
                    'ubicacion': campesino_ubicacion,
                },
            })

        return Response(datos, status=status.HTTP_200_OK)


class GestionListCreateView(RolQuerysetMixin, ListCreateAPIView):
    serializer_class = GestionLogisticaSerializer
    rol_requerido = 'alcaldia'

    def get_queryset(self):
        self.perfil_actual()
        return GestionLogistica.objects.select_related(
            'id_campesino__id_usuario',
        ).order_by('-fecha_asignacion', '-id_gestion')

    def perform_create(self, serializer):
        perfil = self.perfil_actual()
        tipo_residuo = serializer.validated_data.get('tipo_residuo')
        cantidad_kg = serializer.validated_data.get('cantidad_kg')
        campesino = serializer.validated_data.get('id_campesino')

        if not tipo_residuo or cantidad_kg is None:
            raise serializers.ValidationError({'non_field_errors': ['Tipo de residuo y cantidad son obligatorios para la asignación.']})

        ubicacion_entrega = ''
        nombre_campesino = ''
        if campesino and campesino.id_usuario:
            nombre_campesino = campesino.id_usuario.nombre or ''
            ultima_solicitud = (
                SolicitudResiduo.objects
                .filter(id_campesino=campesino)
                .order_by('-fecha_solicitud', '-id_solicitud_residuo')
                .first()
            )
            ubicacion_entrega = (getattr(ultima_solicitud, 'ubicacion', None) or '').strip()

        ubicacion_solicitada = (
            serializer.validated_data.get('ubicacion_entrega')
            or self.request.data.get('ubicacion_entrega')
            or self.request.data.get('ubicacion')
            or ubicacion_entrega
        )
        ubicacion_entrega = str(ubicacion_solicitada or '').strip()

        if not ubicacion_entrega:
            raise serializers.ValidationError({
                'ubicacion_entrega': ['La ubicación de entrega es obligatoria y debe venir del campesino seleccionado.']
            })

        inventario = InventarioAlcaldia.objects.filter(tipo_residuo=tipo_residuo).first()
        cantidad_a_restar = Decimal(str(cantidad_kg))
        solicitud_id = self.request.data.get('solicitud_id') or self.request.data.get('id_solicitud_residuo')

        if solicitud_id:
            try:
                solicitud_id = int(solicitud_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({'solicitud_id': ['El ID de la solicitud de residuo no es válido.']})

        if inventario is None or Decimal(str(inventario.cantidad_total_kg)) < cantidad_a_restar:
            raise serializers.ValidationError({'non_field_errors': ['Inventario insuficiente en la alcaldía para realizar esta asignación.']})

        with transaction.atomic():
            serializer.save(
                id_usuario_alcaldia=perfil,
                ubicacion_entrega=ubicacion_entrega,
            )
            inventario.cantidad_total_kg = Decimal(str(inventario.cantidad_total_kg)) - cantidad_a_restar
            inventario.save(update_fields=['cantidad_total_kg'])

            if solicitud_id:
                solicitud = (
                    SolicitudResiduo.objects.select_for_update()
                    .filter(
                        id_solicitud_residuo=solicitud_id,
                        estado__in=['APROBADO', 'ACEPTADO_POR_CAMPESINO'],
                    )
                    .first()
                )

                if solicitud is None:
                    raise serializers.ValidationError({'solicitud_id': ['La solicitud no existe, no fue aceptada o ya fue asignada.']})

                if campesino and solicitud.id_campesino_id != campesino.id_campesino:
                    raise serializers.ValidationError({'solicitud_id': ['La solicitud no pertenece al campesino seleccionado.']})

                solicitud.estado = 'asignada'
                solicitud.save(update_fields=['estado'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        gestion = serializer.instance
        fecha_entrega = gestion.fecha_asignacion.strftime('%Y-%m-%d %H:%M') if gestion.fecha_asignacion else ''
        nombre_campesino = ''
        if gestion.id_campesino and gestion.id_campesino.id_usuario:
            nombre_campesino = gestion.id_campesino.id_usuario.nombre or ''

        mensaje = (
            f'La alcaldía aceptó tu solicitud. Te va a entregar la cantidad de {gestion.cantidad_kg} kg de residuo '
            f'{gestion.tipo_residuo} al campesino {nombre_campesino} el día {fecha_entrega} en la ubicación {gestion.ubicacion_entrega}.'
        )

        headers = self.get_success_headers(serializer.data)
        return Response({'mensaje': mensaje, 'gestion': serializer.data}, status=status.HTTP_201_CREATED, headers=headers)


class GestionDetailView(RolQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = GestionLogisticaSerializer
    rol_requerido = 'alcaldia'
    lookup_field = 'id_gestion'

    def get_queryset(self):
        self.perfil_actual()
        return GestionLogistica.objects.select_related(
            'id_campesino__id_usuario',
        )

    def perform_update(self, serializer):
        gestion_anterior = self.get_object()
        tipo_anterior = gestion_anterior.tipo_residuo
        cantidad_anterior = gestion_anterior.cantidad_kg or 0

        tipo_nuevo = serializer.validated_data.get('tipo_residuo', tipo_anterior)
        cantidad_nueva = serializer.validated_data.get('cantidad_kg', cantidad_anterior) or 0

        if tipo_anterior == tipo_nuevo:
            diferencia = cantidad_nueva - cantidad_anterior
            if diferencia > 0:
                inventario = InventarioAlcaldia.objects.filter(tipo_residuo=tipo_nuevo).first()
                if inventario is None or inventario.cantidad_total_kg < diferencia:
                    raise serializers.ValidationError({'non_field_errors': ['Inventario insuficiente para aumentar la cantidad de esta asignación.']})
        else:
            inventario_nuevo = InventarioAlcaldia.objects.filter(tipo_residuo=tipo_nuevo).first()
            if inventario_nuevo is None or inventario_nuevo.cantidad_total_kg < cantidad_nueva:
                raise serializers.ValidationError({'non_field_errors': ['Inventario insuficiente en el nuevo tipo de residuo para esta asignación.']})

        ubicacion_solicitada = (
            serializer.validated_data.get('ubicacion_entrega')
            or self.request.data.get('ubicacion_entrega')
            or self.request.data.get('ubicacion')
            or gestion_anterior.ubicacion_entrega
        )

        if not ubicacion_solicitada:
            campesino = serializer.validated_data.get('id_campesino', gestion_anterior.id_campesino)
            if campesino:
                ultima_solicitud = (
                    SolicitudResiduo.objects
                    .filter(id_campesino=campesino)
                    .order_by('-fecha_solicitud', '-id_solicitud_residuo')
                    .first()
                )
                ubicacion_solicitada = (getattr(ultima_solicitud, 'ubicacion', None) or '').strip()

        with transaction.atomic():
            gestion = serializer.save(
                id_usuario_alcaldia=self.perfil_actual(),
                ubicacion_entrega=str(ubicacion_solicitada or '').strip(),
            )

            if tipo_anterior == tipo_nuevo:
                diferencia = cantidad_nueva - cantidad_anterior
                if diferencia > 0:
                    inventario = InventarioAlcaldia.objects.filter(tipo_residuo=tipo_nuevo).first()
                    inventario.cantidad_total_kg -= diferencia
                    inventario.save(update_fields=['cantidad_total_kg'])
                elif diferencia < 0:
                    inventario, _ = InventarioAlcaldia.objects.get_or_create(tipo_residuo=tipo_nuevo)
                    inventario.cantidad_total_kg += abs(diferencia)
                    inventario.save(update_fields=['cantidad_total_kg'])
            else:
                inventario_anterior, _ = InventarioAlcaldia.objects.get_or_create(tipo_residuo=tipo_anterior)
                inventario_anterior.cantidad_total_kg += cantidad_anterior
                inventario_anterior.save(update_fields=['cantidad_total_kg'])

                inventario_nuevo = InventarioAlcaldia.objects.filter(tipo_residuo=tipo_nuevo).first()
                inventario_nuevo.cantidad_total_kg -= cantidad_nueva
                inventario_nuevo.save(update_fields=['cantidad_total_kg'])

    def perform_destroy(self, instance):
        tipo_residuo = instance.tipo_residuo
        cantidad_kg = instance.cantidad_kg or 0
        if tipo_residuo and cantidad_kg > 0:
            inventario, _ = InventarioAlcaldia.objects.get_or_create(tipo_residuo=tipo_residuo)
            inventario.cantidad_total_kg += cantidad_kg
            inventario.save(update_fields=['cantidad_total_kg'])
        instance.delete()


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
            'id_usuario__tipo_usuario',
        )
        return Response({
            'residuos': list(residuos),
            'campesinos': [
                {
                    'id': item['id_campesino'],
                    'username': item['id_usuario__nombre'],
                    'nombre': item['id_usuario__nombre'],
                    'ubicacion': (
                        SolicitudResiduo.objects
                        .filter(id_campesino_id=item['id_campesino'])
                        .order_by('-fecha_solicitud', '-id_solicitud_residuo')
                        .values_list('ubicacion', flat=True)
                        .first()
                    ) or '',
                    'tipo_rol': item['id_usuario__tipo_usuario'],
                }
                for item in campesinos
            ],
        })


class InventarioAlcaldiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = obtener_perfil(request.user)
        if perfil is None or normalizar_rol(perfil.tipo_usuario) != 'alcaldia':
            return Response(
                {'error': 'Solo la alcaldía puede consultar el inventario.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        inventarios = InventarioAlcaldia.objects.all().values('tipo_residuo', 'cantidad_total_kg')
        return Response(list(inventarios), status=status.HTTP_200_OK)
