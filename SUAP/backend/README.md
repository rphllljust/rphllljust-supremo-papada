# SUAP - IDEP

Sistema web em **Django** para gestão escolar, com módulos de:

* usuários
* unidades
* cursos
* turmas
* matrículas

## Requisitos

* Python 3.12+
* pip
* **SQLite** para desenvolvimento
* **PostgreSQL** para produção

## Banco de dados

Atualmente, o projeto está configurado para utilizar **SQLite** durante a etapa de desenvolvimento, por ser mais simples de configurar e executar localmente.

Para o ambiente de **produção**, o banco de dados previsto é o **PostgreSQL**, por oferecer mais robustez, desempenho e recursos adequados para uso em ambiente real.

## Como rodar o projeto no Windows

### 1. Clonar o repositório e entrar na pasta

```powershell
git clone <url-do-repositorio>
cd SUAP
```

### 2. Criar e ativar o ambiente virtual

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

### 3. Instalar as dependências

```powershell
pip install -r requirements.txt
```

### 4. Aplicar as migrações

```powershell
py manage.py migrate
```

### 5. Criar um usuário administrador *(opcional)*

```powershell
py manage.py createsuperuser
```

### 6. Rodar o servidor local

```powershell
py manage.py runserver
```

## Backend Django e frontend React separados

O backend Django passa a ficar desacoplado do frontend React. O fluxo recomendado agora e:

* Django expõe `api/v1/`, `admin/` e as rotas web baseadas em templates
* o frontend React roda separado e consome a API via `VITE_API_URL`
* a integração entre as duas camadas acontece somente por HTTP/API

Para permitir chamadas do frontend externo durante o desenvolvimento, configure CORS no `.env` do Django:

```powershell
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True
```

Suba o backend normalmente:

```powershell
py manage.py runserver
```

Em paralelo, suba o frontend separado:

```powershell
cd ..\frontend
npm install
npm run dev
```

No frontend, defina `VITE_API_URL` apontando para o backend Django, por exemplo:

```text
http://127.0.0.1:8000/api/v1
```

A aplicação ficará disponível em:

```text
http://127.0.0.1:8000/
```

O frontend React em desenvolvimento ficará disponível no host/porta configurados pelo Vite, normalmente:

```text
http://127.0.0.1:5173/
```

## Ambientes: desenvolvimento, homologação e produção

O backend agora suporta três ambientes via `APP_ENV`:

* `development`
* `homolog`
* `production`

Ordem de resolução do arquivo de ambiente no backend:

```text
development: .env.development -> .env -> .env.development.sample -> .env.sample
homolog/production: .env.<ambiente> -> .env.<ambiente>.sample -> .env -> .env.sample
```

Arquivos de exemplo disponíveis:

```text
.env.development.sample
.env.homolog.sample
.env.production.sample
```

Exemplos de execução do backend:

```powershell
cd backend
.\scripts\rodar.ps1 -Environment development
.\scripts\rodar.ps1 -Environment homolog -HostAddress 0.0.0.0 -Port 8001
.\scripts\rodar.ps1 -Environment production -HostAddress 0.0.0.0 -Port 8000
```

No frontend, o Vite usa os modos `development`, `homolog` e `production`, com arquivos `.env` equivalentes:

```text
frontend/.env.development.example
frontend/.env.homolog.example
frontend/.env.production.example
```

Exemplos de execução do frontend:

```powershell
cd ..\frontend
npm.cmd run dev
npm.cmd run dev:homolog
npm.cmd run build:production
```

Django Admin

O Django Admin pode ser utilizado para gerenciar os dados do sistema de forma administrativa, incluindo cadastros e consultas internas.

Após criar um superusuário com o comando abaixo:
```text
py manage.py createsuperuser
```
acesse no navegador:
```text
http://127.0.0.1:8000/admin/
```

## Migrações

### Gerar novas migrações

```powershell
py manage.py makemigrations
```

### Aplicar migrações

```powershell
py manage.py migrate
```

### Verificar pendências de migração

```powershell
py manage.py makemigrations --check --dry-run
```

## Testes

### Rodar toda a suíte de testes

```powershell
py manage.py test
```

### Rodar testes de um app específico

```powershell
py manage.py test apps.cursos
```

## Autenticação da API

A API REST utiliza JWT com `djangorestframework-simplejwt`.

Documento detalhado para integração com AVA:

* [docs/integracao-ava-jwt.md](docs/integracao-ava-jwt.md)

### Obter token

Endpoint:

```text
POST /api/v1/auth/token/
```

Payload:

```json
{
  "cpf": "123.456.789-09",
  "password": "senha123",
  "perfil": "SECRETARIA"
}
```

Resposta esperada:

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
      "claims_version": 1,
      "is_admin": false,
      "module_access": {
        "api": {
          "usuarios": ["view"]
        },
        "api_ava": {
          "usuarios": ["export"]
        },
        "web": {
          "matriculas": ["documents", "flows", "manage", "rule_management", "rules", "transfer_management", "transfers", "view"]
        }
      },
      "permission_claims": [
        "api:usuarios:view",
        "api_ava:usuarios:export",
        "web:matriculas:view"
      ],
      "ava_export_modules": ["matriculas", "turmas", "unidades", "usuarios"]
    }
  }
}
```

### Claims extras no JWT

O `access token` e o `refresh token` carregam claims adicionais calculadas a partir da matriz de acesso:

* `claims_version`: versão do formato das claims retornadas (atual: 1)
* `perfil`
* `is_admin`
* `module_access`
* `permission_claims`
* `ava_export_modules`

### Usar Bearer token

```powershell
curl http://127.0.0.1:8000/api/v1/usuarios/ -H "Authorization: Bearer <access_token>"
```

### Renovar token

Endpoint:

```text
POST /api/v1/auth/token/refresh/
```

Payload:

```json
{
  "refresh": "<refresh_token>"
}
```

### Logout da API

O logout invalida o `refresh token` via blacklist.

Endpoint:

```text
POST /api/v1/auth/logout/
```

Payload:

```json
{
  "refresh": "<refresh_token>"
}
```

### Consultar usuário autenticado

Endpoint:

```text
GET /api/v1/auth/me/
```

### Semântica de resposta

* `401` para requisição sem JWT válido
* `403` para usuário autenticado sem permissão na matriz de acesso

## Estrutura básica

* `apps/` — apps Django do sistema
* `templates/` — templates HTML reutilizáveis e telas de CRUD
* `config/` — configuração principal do projeto (`urls.py`, `settings.py`, etc.)

## Apps principais

* `apps/usuarios`
* `apps/unidades`
* `apps/cursos`
* `apps/turmas`
* `apps/matriculas`
* `apps/dashboard`
* `apps/api`

## Comandos úteis

### Limpar arquivos `.pyc`

```powershell
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force
```

### Abrir o shell do Django

```powershell
py manage.py shell
```

## Observações

* O projeto utiliza **SQLite apenas no ambiente de desenvolvimento**.
* Para **produção**, o banco de dados planejado é o **PostgreSQL**.
* O arquivo `README.md` pode ser expandido futuramente com:

  * padrões de código
  * CI/CD
  * instruções de deploy
* Em caso de alteração nos modelos, execute sempre:

```powershell
py manage.py makemigrations
py manage.py migrate
```
