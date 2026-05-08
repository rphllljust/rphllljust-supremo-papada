from django.urls import path

from .views import (
    SuapAuthStartApiView,
    SuapAuthCallbackView,
    SuapTicketExchangeApiView,
    SuapWhoAmIApiView,
)

urlpatterns = [
    path("auth/start/", SuapAuthStartApiView.as_view(), name="suap_auth_start"),
    path("auth/callback/", SuapAuthCallbackView.as_view(), name="suap_auth_callback"),
    path("auth/exchange-ticket/", SuapTicketExchangeApiView.as_view(), name="suap_auth_exchange_ticket"),
    path("me/", SuapWhoAmIApiView.as_view(), name="suap_me"),
]
