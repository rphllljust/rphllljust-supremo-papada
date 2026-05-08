import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .services import SuapIntegrationError, build_authorize_url, exchange_code_for_token, fetch_me, generate_state

logger = logging.getLogger(__name__)
User = get_user_model()


class SuapAuthStartApiView(APIView):
    def get(self, request):
        state = generate_state()
        cache.set(f"suap:oauth_state:{state}", True, timeout=300)
        return Response({"authorize_url": build_authorize_url(state)})


class SuapAuthCallbackView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state or not cache.get(f"suap:oauth_state:{state}"):
            return HttpResponseRedirect(f"{settings.SUAP_FRONTEND_CALLBACK_URL}?status=error&reason=invalid_state")

        cache.delete(f"suap:oauth_state:{state}")

        try:
            token_data = exchange_code_for_token(code)
            suap_user = fetch_me(token_data.get("access_token", ""))
        except SuapIntegrationError as exc:
            logger.exception("Erro na autenticacao SUAP: %s", exc)
            return HttpResponseRedirect(f"{settings.SUAP_FRONTEND_CALLBACK_URL}?status=error&reason=oauth_exchange")

        cpf = (suap_user.get("cpf") or "").replace(".", "").replace("-", "")
        username = suap_user.get("username") or cpf
        if not cpf:
            return HttpResponseRedirect(f"{settings.SUAP_FRONTEND_CALLBACK_URL}?status=error&reason=missing_cpf")

        user, _ = User.objects.get_or_create(
            cpf=cpf,
            defaults={
                "username": username,
                "first_name": suap_user.get("first_name", ""),
                "last_name": suap_user.get("last_name", ""),
                "tipo": "SECRETARIA",
            },
        )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_token = str(refresh)

        ticket = secrets.token_urlsafe(24)
        cache.set(
            f"suap:login_ticket:{ticket}",
            {
                "access": access,
                "refresh": refresh_token,
                "suap_access_token": token_data.get("access_token"),
            },
            timeout=180,
        )
        return HttpResponseRedirect(f"{settings.SUAP_FRONTEND_CALLBACK_URL}?status=success&ticket={ticket}")


class SuapWhoAmIApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suap_token = cache.get(f"suap:token:user:{request.user.id}")
        if not suap_token:
            return Response({"detail": "Usuario sem token SUAP ativo. Faca login com SUAP novamente."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            data = fetch_me(suap_token)
        except SuapIntegrationError as exc:
            logger.exception("Falha ao consultar SUAP /me: %s", exc)
            return Response({"detail": "Falha ao consultar SUAP."}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(data)


class SuapTicketExchangeApiView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        ticket = request.data.get("ticket")
        if not ticket:
            return Response({"detail": "Ticket obrigatorio."}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"suap:login_ticket:{ticket}"
        payload = cache.get(cache_key)
        if not payload:
            return Response({"detail": "Ticket invalido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)
        cache.delete(cache_key)

        refresh = RefreshToken(payload["refresh"])
        cache.set(f"suap:token:user:{refresh['user_id']}", payload.get("suap_access_token"), timeout=3600)

        return Response({"access": payload["access"], "refresh": payload["refresh"]})
