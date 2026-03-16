from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.AccountsLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("logout/confirmado/", views.logout_confirmado, name="logout_confirmado"),
    path("password-change/", views.AccountsPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", views.AccountsPasswordChangeDoneView.as_view(), name="password_change_done"),

    path("register/", views.cadastro, name="register"),

    path("password-reset/", views.AccountsPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.AccountsPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.AccountsPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.AccountsPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
