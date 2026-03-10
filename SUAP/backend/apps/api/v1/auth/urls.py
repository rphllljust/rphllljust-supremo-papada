from django.urls import path

from .views import AuthLogoutApiView, AuthMeApiView, AuthSessionApiView, PerfilTokenObtainPairView, PerfilTokenRefreshView

app_name = "api_v1_auth"

urlpatterns = [
    path("token/", PerfilTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", PerfilTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", AuthLogoutApiView.as_view(), name="logout"),
    path("session/", AuthSessionApiView.as_view(), name="session"),
    path("me/", AuthMeApiView.as_view(), name="me"),
]
