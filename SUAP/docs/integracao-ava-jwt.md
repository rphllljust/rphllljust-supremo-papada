# Integração AVA com JWT

Este documento descreve como um cliente HTTP externo, como um AVA, deve autenticar, renovar token, consultar identidade e chamar os endpoints protegidos da API.

## Visão geral

O projeto usa autenticação JWT com `djangorestframework-simplejwt`.

Regras importantes:

* autenticação da API é separada do login web
* o login da API exige `cpf`, `password` e `perfil`
* o token já devolve claims derivadas da matriz de acesso por perfil
* a autorização continua centralizada no app `access`

## Endpoints de autenticação

### Obter token

`POST /api/v1/auth/token/`

Payload:

```json
{
  "cpf": "123.456.789-09",
  "password": "senha123",
  "perfil": "SECRETARIA"
}
```

Resposta de exemplo:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>",
  "user": {
    "id": 1,
    "cpf": "12345678909",
    "perfil": "SECRETARIA",
    "username": "12345678909",
    "first_name": "Ana",
    "last_name": "Secretaria",
    "access_context": {
      "is_admin": false,
      "module_access": {
        "api": {
          "usuarios": ["view"],
          "turmas": ["view"],
          "matriculas": ["view"],
          "unidades": ["view"]
        },
        "api_ava": {
          "usuarios": ["export"],
          "turmas": ["export"],
          "matriculas": ["export"],
          "unidades": ["export"]
        },
        "web": {
          "dashboard": ["view"],
          "usuarios": ["manage", "view"]
        }
      },
      "permission_claims": [
        "api:matriculas:view",
        "api:turmas:view",
        "api:unidades:view",
        "api:usuarios:view",
        "api_ava:matriculas:export",
        "api_ava:turmas:export",
        "api_ava:unidades:export",
        "api_ava:usuarios:export"
      ],
      "ava_export_modules": [
        "matriculas",
        "turmas",
        "unidades",
        "usuarios"
      ]
    }
  }
}
```

### Renovar token

`POST /api/v1/auth/token/refresh/`

Payload:

```json
{
  "refresh": "<refresh_token>"
}
```

Resposta de exemplo:

```json
{
  "access": "<new_access_token>",
  "refresh": "<new_refresh_token>"
}
```

### Logout da API

`POST /api/v1/auth/logout/`

Headers:

```text
Authorization: Bearer <access_token>
```

Payload:

```json
{
  "refresh": "<refresh_token>"
}
```

O endpoint invalida o `refresh token` por blacklist. Depois disso, ele nao deve mais ser aceito no endpoint de refresh.

### Consultar identidade autenticada

`GET /api/v1/auth/me/`

Headers:

```text
Authorization: Bearer <access_token>
```

Esse endpoint retorna os dados do usuario autenticado e o mesmo `access_context` calculado a partir do perfil.

## Claims extras do JWT

Os tokens emitidos incluem claims extras para facilitar integrações e auditoria:

* `cpf`: CPF normalizado do usuario
* `perfil`: perfil autenticado no momento do login
* `is_admin`: se o usuario possui acesso administrativo efetivo
* `module_access`: mapa por superficie e modulo com as acoes permitidas
* `permission_claims`: lista linearizada no formato `surface:module:action`
* `ava_export_modules`: lista dos modulos que o perfil pode exportar para o AVA

## Exemplos com curl

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"cpf":"123.456.789-09","password":"senha123","perfil":"SECRETARIA"}'
```

### Chamada autenticada

```bash
curl http://127.0.0.1:8000/api/v1/usuarios/ \
  -H "Authorization: Bearer <access_token>"
```

### Refresh

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

### Logout

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

## Semântica HTTP

* `200`: autenticado e autorizado
* `400`: payload inválido no login, refresh ou logout
* `401`: token ausente, inválido ou expirado
* `403`: autenticado, mas sem permissão na matriz de acesso

## Observações operacionais

* o AVA deve armazenar o `refresh token` em local seguro
* o `access token` deve ser enviado sempre como `Authorization: Bearer ...`
* quando o `access token` expirar, o cliente deve usar o `refresh token` para obter um novo par de tokens
* após logout, o `refresh token` anterior nao deve mais ser reutilizado