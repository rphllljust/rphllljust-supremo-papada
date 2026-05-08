# SUAP - IDEP

Sistema web em **Django** para gestão escolar, com módulos de:

* usuários
* unidades
* cursos
* turmas
* matrículas
* **PostgreSQL** para desenvolvimento, homologação e produção

* Python 3.12+
* pip
Todos os ambientes agora usam **PostgreSQL**, mas o Compose foi separado por perfil operacional usando arquivos específicos:

* `docker-compose.yml` -> base compartilhada
* `docker-compose.development.yml` -> desenvolvimento
* `docker-compose.homolog.yml` -> homologação
* `docker-compose.production.yml` -> produção

Com isso, cada ambiente tem portas, modo de frontend e credenciais próprias, sem misturar configuração.

Para subir o ambiente de **desenvolvimento** completo:

Nos ambientes de **homologação** e **produção**, o banco previsto é **PostgreSQL**.

docker compose -p suap-dev -f docker-compose.yml -f docker-compose.development.yml up -d --build

Para subir o ambiente de desenvolvimento completo:
Para subir **homologação** local:
```powershell
cd ..\..
docker compose up -d --build backend frontend
docker compose -p suap-homolog -f docker-compose.yml -f docker-compose.homolog.yml up -d --build

Ou simplesmente:
Para subir **produção** local:
```powershell
```powershell
cd ..\..
docker compose -p suap-prod -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Portas previstas por ambiente:

```text
development: postgres 5432, backend 8000, frontend 5173
homolog:     postgres 5433, backend 8001, frontend 5174
production:  postgres 5434, backend 8002, frontend 4173
```

## Como rodar o projeto no Windows

### 1. Clonar o repositório e entrar na pasta
docker compose up -d --build
```powershell
git clone <url-do-repositorio>
cd SUAP
Nesse modo, o backend usa o `db.sqlite3` montado do diretório [SUAP/backend](c:\Users\jacja\Documents\github\suap-idep\SUAP\backend) e o frontend fica disponível em `http://127.0.0.1:5173/`.


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

### 3.1. Subir desenvolvimento com Docker Compose

```powershell
cd ..\..
docker compose -p suap-dev -f docker-compose.yml -f docker-compose.development.yml up -d --build
cd SUAP\backend
```

### 4. Aplicar as migrações

```powershell
py manage.py migrate
```

### 4.1. Popular o banco de desenvolvimento

```powershell
.\scripts\popular_banco.ps1 -Reset
```

Esse comando cria usuários, cursos, turmas, matrículas, notas, frequências, edital e processo de exemplo no banco atualmente configurado. Em `development`, isso significa o Postgres de desenvolvimento.

Agora o seed também cria uma base acadêmica mais completa para desenvolvimento, sem depender do AVA/Moodle, incluindo diários, materiais de aula e ocorrências para duas turmas de exemplo.

Usuários padrão do seed:

```text
admin.dev / admin123
secretaria.dev / secretaria123
coordenacao.dev / coordenacao123
professor.dev / professor123
professor.dev.2 / professor123
aluno.dev.1 / aluno123
aluno.dev.2 / aluno123
aluno.dev.3 / aluno123
aluno.dev.4 / aluno123
```

### 4.2. Migrar um SQLite existente para o Postgres

```powershell
.\scripts\migrar_sqlite_para_postgres.ps1 -Environment development -SqlitePath db.sqlite3
```

Esse comando foi pensado para levar uma base SQLite legada para qualquer ambiente Postgres configurado. Por padrão ele limpa o Postgres de destino antes da carga. Para preservar dados atuais, passe `-FlushTarget $false`.

### 5. Criar um usuário administrador *(opcional)*

```powershell
py manage.py createsuperuser
```

### 5.1. Bootstrap do administrador inicial

```powershell
py manage.py bootstrap_initial_admin
```

O comando acima cria o administrador inicial usando os valores de `INITIAL_ADMIN_CPF`, `INITIAL_ADMIN_PASSWORD`, `INITIAL_ADMIN_FIRST_NAME` e `INITIAL_ADMIN_LAST_NAME` definidos no `.env` do ambiente. Se o usuario ja existir, ele e preservado. Para recriar explicitamente o administrador inicial, use `py manage.py bootstrap_initial_admin --force`. Por padrao ele marca o usuario com troca obrigatoria de senha no primeiro acesso.

O CPF do administrador inicial agora precisa estar configurado explicitamente em `INITIAL_ADMIN_CPF` ou ser informado via `--cpf`; o comando nao usa mais fallback hardcoded.

Politica de primeiro acesso:

* contas com `must_change_password=True` sao redirecionadas para a troca de senha no login web do Django
* a API JWT tambem expõe `must_change_password` no payload do usuario e em `/api/v1/auth/me`
* o frontend React bloqueia a navegacao comum ate a senha ser alterada em `/comum/alterar-senha`

### 5.2. Preparacao para integracao com Moodle

O backend agora traz uma base organizada para consumo da API externa do Moodle no app `apps.integracao_moodle`.

Configuracoes disponiveis no `.env`:

```text
MOODLE_API_BASE_URL=
MOODLE_API_REST_PATH=webservice/rest/server.php
MOODLE_API_TOKEN=
MOODLE_API_TIMEOUT=30
MOODLE_API_VERIFY_SSL=False
MOODLE_API_WS_FORMAT=json
```

Organizacao inicial:

* `apps.integracao_moodle.schemas.MoodleApiSettings` centraliza a configuracao
* `apps.integracao_moodle.client.MoodleApiClient` concentra as chamadas REST
* `apps.integracao_moodle.services.get_moodle_api_client()` vira o ponto de entrada para os futuros casos de uso
* `apps.integracao_moodle.exceptions` isola os erros especificos da integracao

Escopo atual aprovado de funcoes Moodle:

* `core_course_get_categories`
* `core_course_get_courses`
* `core_grades_get_grade_tree`
* `core_grades_get_gradeitems`
* `core_grades_update_grades`
* `gradereport_user_get_grade_items`
* `gradereport_user_get_grades_table`
* `mod_assign_save_grade`
* `mod_assign_save_grades`

Qualquer `wsfunction` fora dessa lista passa a ser bloqueada pelo client ate nova revisao do escopo.

Persistencia local ja preparada:

* espelho de categorias em `MoodleCategory`
* espelho de cursos em `MoodleCourse`, com vinculo para categoria Moodle e para `Curso` quando existir correspondencia
* snapshots de consultas de notas em `MoodleGradeSnapshot`
* logs de escrita em `MoodleWritebackLog`

Comandos administrativos disponiveis:

* `python manage.py testar_integracao_moodle`
* `python manage.py sincronizar_categorias_moodle`
* `python manage.py sincronizar_catalogo_moodle`
* `python manage.py importar_cursos_moodle --unidade-codigo sede`

Guia rapido: `docs/integracao-moodle-api.md`

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

### 5.3. Historico escolar digital (MEC/XSD)

Foi adicionada uma camada digital complementar para historicos escolares, sem alterar as estruturas legadas:

* modelo `HistoricoEscolarDigital`
* emissao XML em namespace MEC
* validacao XSD
* assinatura XMLDSig (opcional por ambiente)
* PDF + chave de autenticacao + QR Code
* segunda via rastreavel
* auditoria de emissao/revogacao

Documentacao operacional:

* `docs/historico-digital-mec.md`

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
http://localhost:8010/api/v1
```

A aplicação ficará disponível em:

```text
http://localhost:8010/
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

Todos os arquivos de ambiente do backend usam PostgreSQL; o que muda entre eles é base, credencial, host/porta e flags de segurança.

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

Exemplos de execução via Compose por ambiente:

```powershell
docker compose -p suap-dev -f docker-compose.yml -f docker-compose.development.yml up -d --build
docker compose -p suap-homolog -f docker-compose.yml -f docker-compose.homolog.yml up -d --build
docker compose -p suap-prod -f docker-compose.yml -f docker-compose.production.yml up -d --build
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
http://localhost:8010/admin/
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
curl http://localhost:8010/api/v1/usuarios/ -H "Authorization: Bearer <access_token>"
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

* O backend agora aceita sobrescrever configurações por variáveis de ambiente reais, além dos arquivos `.env*`.
* O projeto usa **PostgreSQL** nos três ambientes; o `db.sqlite3` pode ser usado como origem para carga histórica via script.
* O arquivo `README.md` pode ser expandido futuramente com:

  * padrões de código
  * CI/CD
  * instruções de deploy
* Em caso de alteração nos modelos, execute sempre:

```powershell
py manage.py makemigrations
py manage.py migrate
```
