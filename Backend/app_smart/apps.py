from django.apps import AppConfig
from django.db.models.signals import post_migrate


ADMIN_USERNAME = 'fandefangs'
ADMIN_EMAIL = 'fabiantfandi@gmail.com'
ADMIN_PASSWORD = 'Mako55ty'
ADMIN_ROLE = 'admin'


def crear_o_actualizar_admin(sender, **kwargs):
    if getattr(sender, 'name', '') != 'app_smart':
        return

    from django.contrib.auth.models import User
    from .models import Usuario

    usuario_auth = (
        User.objects.filter(username=ADMIN_USERNAME).first()
        or User.objects.filter(email__iexact=ADMIN_EMAIL).first()
    )

    if usuario_auth is None:
        usuario_auth = User(username=ADMIN_USERNAME, email=ADMIN_EMAIL)

    correo_anterior = usuario_auth.email
    usuario_auth.username = ADMIN_USERNAME
    usuario_auth.email = ADMIN_EMAIL
    usuario_auth.first_name = 'Administrador'
    usuario_auth.is_staff = True
    usuario_auth.is_superuser = True
    usuario_auth.is_active = True
    usuario_auth.set_password(ADMIN_PASSWORD)
    usuario_auth.save()

    perfil = (
        Usuario.objects.filter(correo__iexact=ADMIN_EMAIL).first()
        or Usuario.objects.filter(correo__iexact=correo_anterior).first()
    )
    if perfil is None:
        perfil = Usuario.objects.create(
            nombre='Administrador',
            correo=ADMIN_EMAIL,
            tipo_usuario=ADMIN_ROLE,
            estado_cuenta='ACEPTADO',
        )
    else:
        perfil.nombre = 'Administrador'
        perfil.correo = ADMIN_EMAIL
        perfil.tipo_usuario = ADMIN_ROLE
        perfil.estado_cuenta = 'ACEPTADO'
        perfil.save(update_fields=['nombre', 'correo', 'tipo_usuario', 'estado_cuenta'])


class AppSmartConfig(AppConfig):
    name = 'app_smart'

    def ready(self):
        post_migrate.connect(
            crear_o_actualizar_admin,
            sender=self,
            dispatch_uid='app_smart.crear_o_actualizar_admin',
        )
