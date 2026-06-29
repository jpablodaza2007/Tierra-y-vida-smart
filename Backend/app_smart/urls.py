from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ActivarCuentaView,
    AprobarCuentaView,
    AprobarUsuarioView,
    AuditoriaResiduoDecisionView,
    AuditoriaResiduoListView,
    GestionDetailView,
    GestionListCreateView,
    GoogleLoginView,
    InventarioAlcaldiaView,
    MisAsignacionesView,
    LoginView,
    OpcionesLogisticaView,
    PerfilView,
    RegistroUsuarioView,
    ResiduoDetailView,
    ResiduoDisponibleView,
    ResiduoListCreateView,
    SensorDetailView,
    SensorListCreateView,
    SolicitudResiduoView,
    SolicitudSensorView,
)

urlpatterns = [
    path('auth/register/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),

    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),

    path('auth/activate/', ActivarCuentaView.as_view(), name='activar_cuenta'),
    path('auth/aprobar-cuenta/', AprobarCuentaView.as_view(), name='aprobar_cuenta'),
    
    path('auth/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', PerfilView.as_view(), name='perfil'),
    path('usuarios/<int:id_usuario>/aprobar/', AprobarUsuarioView.as_view(), name='aprobar_usuario'),

    path('residuos/', ResiduoListCreateView.as_view(), name='residuos'),
    path('residuos-auditoria/', AuditoriaResiduoListView.as_view(), name='residuos_auditoria'),
    path('residuos-auditoria/<int:id_residuo>/decision/', AuditoriaResiduoDecisionView.as_view(), name='residuos_auditoria_decision'),
    path('residuos-disponibles/', ResiduoDisponibleView.as_view(), name='residuos_disponibles'),
    path('residuos/<int:id_residuo>/', ResiduoDetailView.as_view(), name='residuo_detalle'),
    path('solicitudes-sensor/', SolicitudSensorView.as_view(), name='solicitudes_sensor'),
    path('solicitudes-residuo/', SolicitudResiduoView.as_view(), name='solicitudes_residuo'),
    path('sensores/', SensorListCreateView.as_view(), name='sensores'),
    path('sensores/<int:id_sensor>/', SensorDetailView.as_view(), name='sensor_detalle'),
    path('mis-asignaciones/', MisAsignacionesView.as_view(), name='mis_asignaciones'),
    path('gestiones/', GestionListCreateView.as_view(), name='gestiones'),
    path('gestiones/<int:id_gestion>/', GestionDetailView.as_view(), name='gestion_detalle'),
    path('opciones-logistica/', OpcionesLogisticaView.as_view(), name='opciones_logistica'),
    path('inventario-alcaldia/', InventarioAlcaldiaView.as_view(), name='inventario_alcaldia'),
]
