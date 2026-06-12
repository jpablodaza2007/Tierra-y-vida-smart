from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegistroUsuarioView

urlpatterns = [
    path('auth/register/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('auth/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]