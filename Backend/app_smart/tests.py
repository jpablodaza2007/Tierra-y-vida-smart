from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from .models import Campesino, Contribuyente, ResiduoOrganico, SolicitudResiduo, Usuario
from .views import crear_token_verificacion


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_URL='http://localhost:4200',
)
class VerificacionCorreoTests(APITestCase):
    def test_registro_crea_usuario_inactivo_y_envia_correo(self):
        respuesta = self.client.post(
            reverse('registro_usuario'),
            {
                'username': 'campesino1',
                'email': 'campesino@example.com',
                'password': 'UnaClaveSegura123',
                'nombre_completo': 'Campesino Uno',
                'tipo_rol': 'Campesino',
            },
            format='json',
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_201_CREATED,
            respuesta.data,
        )
        self.assertFalse(User.objects.get(username='campesino1').is_active)
        self.assertTrue(Usuario.objects.filter(correo='campesino@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/activar-cuenta?token=', mail.outbox[0].body)

    def test_usuario_inactivo_no_puede_iniciar_sesion(self):
        User.objects.create_user(
            username='pendiente',
            email='pendiente@example.com',
            password='UnaClaveSegura123',
            is_active=False,
        )

        respuesta = self.client.post(
            reverse('token_obtain_pair'),
            {
                'username': 'pendiente',
                'password': 'UnaClaveSegura123',
            },
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('confirmar tu correo', str(respuesta.data['detail']))

    def test_enlace_valido_activa_usuario(self):
        usuario = User.objects.create_user(
            username='poractivar',
            email='poractivar@example.com',
            password='UnaClaveSegura123',
            is_active=False,
        )
        token = crear_token_verificacion(usuario)

        respuesta = self.client.get(
            reverse('activar_cuenta'),
            {'token': token},
        )

        usuario.refresh_from_db()
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertTrue(usuario.is_active)

    def test_enlace_alterado_es_rechazado(self):
        respuesta = self.client.get(
            reverse('activar_cuenta'),
            {'token': 'token-alterado'},
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('app_smart.views.send_mail', side_effect=RuntimeError('SMTP no disponible'))
    def test_fallo_de_correo_no_deja_cuenta_incompleta(self, _send_mail):
        respuesta = self.client.post(
            reverse('registro_usuario'),
            {
                'username': 'sincorreo',
                'email': 'sincorreo@example.com',
                'password': 'UnaClaveSegura123',
                'nombre_completo': 'Sin Correo',
                'tipo_rol': 'Campesino',
            },
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(User.objects.filter(username='sincorreo').exists())
        self.assertFalse(Usuario.objects.filter(correo='sincorreo@example.com').exists())


class AutenticacionYRegistroTests(APITestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('app_smart.views.id_token.verify_oauth2_token')
    def test_google_login_rechaza_correos_no_registrados(self, mock_verify):
        mock_verify.return_value = {
            'email': 'nuevo@example.com',
            'email_verified': True,
            'name': 'Nuevo Usuario',
        }

        respuesta = self.client.post(
            reverse('google_login'),
            {'token': 'token-fake'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('registrarse formalmente', str(respuesta.data['error']))
        self.assertFalse(User.objects.filter(email='nuevo@example.com').exists())

    def test_registro_con_comprobante_para_alcaldia_queda_pendiente(self):
        comprobante = SimpleUploadedFile(
            'comprobante.pdf',
            b'%PDF-1.4\n',
            content_type='application/pdf',
        )

        respuesta = self.client.post(
            reverse('registro_usuario'),
            {
                'username': 'alcaldia1',
                'email': 'alcaldia@example.com',
                'password': 'UnaClaveSegura123',
                'nombre_completo': 'Alcaldía Uno',
                'tipo_rol': 'Alcaldía',
                'comprobante_registro': comprobante,
            },
            format='multipart',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        usuario_django = User.objects.get(username='alcaldia1')
        self.assertFalse(usuario_django.is_active)
        perfil = Usuario.objects.get(correo='alcaldia@example.com')
        self.assertEqual(perfil.estado_cuenta, 'pendiente_aprobacion')
        self.assertTrue(bool(perfil.comprobante_registro))


class CrudPorRolTests(APITestCase):
    def crear_usuario(self, username, rol):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='UnaClaveSegura123',
        )
        perfil = Usuario.objects.create(
            nombre=username.title(),
            correo=user.email,
            tipo_usuario=rol,
        )
        return user, perfil

    def test_contribuyente_administra_sus_residuos(self):
        user, perfil = self.crear_usuario('contribuyente', 'Contribuyente')
        Contribuyente.objects.create(id_usuario=perfil)
        self.client.force_authenticate(user)

        crear = self.client.post(
            reverse('residuos'),
            {'tipo_residuo': 'Cáscaras', 'cantidad_kg': '12.50'},
            format='json',
        )
        listar = self.client.get(reverse('residuos'))

        self.assertEqual(crear.status_code, status.HTTP_201_CREATED)
        self.assertEqual(listar.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listar.data), 1)
        self.assertEqual(listar.data[0]['estado'], 'Pendiente')

    def test_campesino_administra_sus_sensores(self):
        user, perfil = self.crear_usuario('campesino', 'Campesino')
        Campesino.objects.create(id_usuario=perfil)
        self.client.force_authenticate(user)

        crear = self.client.post(
            reverse('sensores'),
            {'tipo_sensor': 'Humedad'},
            format='json',
        )
        prohibido = self.client.get(reverse('residuos'))

        self.assertEqual(crear.status_code, status.HTTP_201_CREATED)
        self.assertEqual(prohibido.status_code, status.HTTP_403_FORBIDDEN)

    def test_campesino_puede_solicitar_sensor_y_envia_correo_admin(self):
        user, perfil = self.crear_usuario('solicitante', 'Campesino')
        Campesino.objects.create(id_usuario=perfil)
        contrib_user, contrib_perfil = self.crear_usuario('donante', 'Contribuyente')
        contribuyente = Contribuyente.objects.create(id_usuario=contrib_perfil)
        residuo = ResiduoOrganico.objects.create(
            id_contribuyente=contribuyente,
            tipo_residuo='Restos vegetales',
            cantidad_kg=20,
            estado='Disponible',
        )
        self.client.force_authenticate(user)

        respuesta = self.client.post(
            reverse('solicitudes_sensor'),
            {
                'tipo_sensor': 'Humedad',
                'id_residuo': residuo.id_residuo,
            },
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Solicitud de sensor', mail.outbox[0].subject)

    def test_campesino_solicita_residuo_y_queda_pendiente_para_alcaldia(self):
        user, perfil = self.crear_usuario('campesino_residuo', 'Campesino')
        campesino = Campesino.objects.create(id_usuario=perfil)
        contrib_user, contrib_perfil = self.crear_usuario('donante', 'Contribuyente')
        contribuyente = Contribuyente.objects.create(id_usuario=contrib_perfil)
        residuo = ResiduoOrganico.objects.create(
            id_contribuyente=contribuyente,
            tipo_residuo='Restos vegetales',
            cantidad_kg=20,
            estado='Disponible',
        )
        _ = contrib_user
        self.client.force_authenticate(user)

        respuesta = self.client.post(
            reverse('solicitudes_residuo'),
            {'id_residuo': residuo.id_residuo},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            SolicitudResiduo.objects.filter(id_campesino=campesino, id_residuo=residuo, estado='pendiente').exists()
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_alcaldia_asigna_residuo_a_campesino(self):
        contrib_user, contrib_perfil = self.crear_usuario('donante', 'Contribuyente')
        contribuyente = Contribuyente.objects.create(id_usuario=contrib_perfil)
        residuo = ResiduoOrganico.objects.create(
            id_contribuyente=contribuyente,
            tipo_residuo='Restos vegetales',
            cantidad_kg=20,
            estado='Pendiente',
        )
        _ = contrib_user

        _, campesino_perfil = self.crear_usuario('receptor', 'Campesino')
        campesino = Campesino.objects.create(id_usuario=campesino_perfil)
        alcaldia_user, _ = self.crear_usuario('alcaldia', 'Alcaldia')
        self.client.force_authenticate(alcaldia_user)

        respuesta = self.client.post(
            reverse('gestiones'),
            {
                'id_residuo_id': residuo.id_residuo,
                'id_campesino_id': campesino.id_campesino,
                'fecha_asignacion': '2026-06-20T10:00:00Z',
            },
            format='json',
        )

        residuo.refresh_from_db()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(residuo.estado, 'Asignado')

    def test_aprobacion_de_cuenta_activa_usuario_y_actualiza_estado(self):
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='UnaClaveSegura123',
            is_staff=True,
        )
        user, perfil = self.crear_usuario('pendiente', 'Campesino')
        perfil.estado_cuenta = 'pendiente_aprobacion'
        perfil.save(update_fields=['estado_cuenta'])
        self.client.force_authenticate(admin)

        respuesta = self.client.post(
            reverse('aprobar_cuenta'),
            {'usuario_id': user.pk},
            format='json',
        )

        user.refresh_from_db()
        perfil.refresh_from_db()
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertTrue(user.is_active)
        self.assertEqual(perfil.estado_cuenta, 'aprobado')
        self.assertEqual(len(mail.outbox), 1)
