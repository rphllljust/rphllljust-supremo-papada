from django.urls import path

from .views import AuthChangePasswordApiView, AuthLogoutApiView, AuthMeApiView, PerfilTokenObtainPairView, PerfilTokenRefreshView

app_name = "api_v1_auth"

urlpatterns = [
    path("token/", PerfilTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", PerfilTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", AuthLogoutApiView.as_view(), name="logout"),
    path("change-password/", AuthChangePasswordApiView.as_view(), name="change-password"),
    path("me/", AuthMeApiView.as_view(), name="me"),
]
