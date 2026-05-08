# Integracao SUAP (OAuth2)

## Variaveis de ambiente
Defina no backend:

- `SUAP_AUTHORIZE_URL`
- `SUAP_TOKEN_URL`
- `SUAP_USERINFO_URL`
- `SUAP_CLIENT_ID`
- `SUAP_CLIENT_SECRET`
- `SUAP_REDIRECT_URI`
- `SUAP_SCOPE`
- `SUAP_TIMEOUT`
- `SUAP_FRONTEND_CALLBACK_URL`

## Fluxo
1. Frontend chama `GET /api/v1/suap/auth/start/`.
2. Backend devolve URL de autorizacao SUAP com `state`.
3. Usuario autentica no SUAP e retorna em `SUAP_REDIRECT_URI`.
4. Callback troca `code` por token no backend e cria `ticket` temporario.
5. Frontend recebe `ticket` e chama `POST /api/v1/suap/auth/exchange-ticket/` para obter JWT local.
6. Consultas ao SUAP sao feitas pelo backend (`GET /api/v1/suap/me/`).

## Seguranca
- `client_secret` nunca vai ao frontend.
- Senha do SUAP nao e armazenada.
- Token SUAP e mantido temporariamente no cache do servidor.
