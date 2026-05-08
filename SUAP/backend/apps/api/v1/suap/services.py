import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings


class SuapIntegrationError(Exception):
    pass


def build_authorize_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.SUAP_CLIENT_ID,
        "redirect_uri": settings.SUAP_REDIRECT_URI,
        "scope": settings.SUAP_SCOPE,
        "state": state,
    }
    return f"{settings.SUAP_AUTHORIZE_URL}?{urlencode(params)}"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def exchange_code_for_token(code: str) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SUAP_REDIRECT_URI,
        "client_id": settings.SUAP_CLIENT_ID,
        "client_secret": settings.SUAP_CLIENT_SECRET,
    }
    response = requests.post(settings.SUAP_TOKEN_URL, data=payload, timeout=settings.SUAP_TIMEOUT)
    if response.status_code >= 400:
        raise SuapIntegrationError(f"Erro ao trocar codigo por token no SUAP: {response.status_code}")
    return response.json()


def fetch_me(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(settings.SUAP_USERINFO_URL, headers=headers, timeout=settings.SUAP_TIMEOUT)
    if response.status_code >= 400:
        raise SuapIntegrationError(f"Erro ao consultar endpoint de usuario do SUAP: {response.status_code}")
    return response.json()
