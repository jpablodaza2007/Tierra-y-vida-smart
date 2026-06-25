from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ActivarCuentaView,
    AprobarUsuarioView,
    GestionDetailView,
    GestionListCreateView,
    GoogleLoginView,
    LoginView,
    OpcionesLogisticaView,
    PerfilView,
    RegistroUsuarioView,
    ResiduoDetailView,
    ResiduoListCreateView,
    SensorDetailView,
    SensorListCreateView,
)

urlpatterns = [
    path('auth/register/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),

    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),

    path('auth/activate/', ActivarCuentaView.as_view(), name='activar_cuenta'),
    
    path('auth/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', PerfilView.as_view(), name='perfil'),
    path('usuarios/<int:id_usuario>/aprobar/', AprobarUsuarioView.as_view(), name='aprobar_usuario'),

    path('residuos/', ResiduoListCreateView.as_view(), name='residuos'),
    path('residuos/<int:id_residuo>/', ResiduoDetailView.as_view(), name='residuo_detalle'),
    path('sensores/', SensorListCreateView.as_view(), name='sensores'),
    path('sensores/<int:id_sensor>/', SensorDetailView.as_view(), name='sensor_detalle'),
    path('gestiones/', GestionListCreateView.as_view(), name='gestiones'),
    path('gestiones/<int:id_gestion>/', GestionDetailView.as_view(), name='gestion_detalle'),
    path('opciones-logistica/', OpcionesLogisticaView.as_view(), name='opciones_logistica'),
]
