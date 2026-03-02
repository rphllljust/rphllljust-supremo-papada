# Plano: SUAP ETEC-IDEP — Projeto Django com OAuth2

## Contexto
Criação do sistema SUAP da ETEC-IDEP, uma aplicação web Django com autenticação OAuth2 via SUAP (suap.ifrn.edu.br). O projeto inclui módulos de Dashboard, Perfil de Usuário e Notícias/Avisos, utilizando social-auth-app-django, django-environ, Ruff e Djlint.

---

## Estrutura do Projeto

```
C:\Users\rphll\etec-idep-suap\
├── .env.example
├── .gitignore
├── pyproject.toml          # Ruff + Djlint config
├── requirements.txt
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── models.py       # CustomUser estendendo AbstractUser
│   │   ├── views.py        # login, logout, profile
│   │   ├── urls.py
│   │   └── pipeline.py     # social-auth pipeline: salvar dados do SUAP
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── urls.py
│   └── news/
│       ├── __init__.py
│       ├── admin.py
│       ├── models.py       # News (titulo, conteudo, data, autor)
│       ├── views.py
│       └── urls.py
├── templates/
│   ├── base.html           # Layout base com navbar + sidebar
│   ├── home.html           # Landing page pública
│   ├── accounts/
│   │   ├── login.html      # Botão "Entrar com SUAP"
│   │   └── profile.html    # Dados do usuário vindos do SUAP
│   ├── dashboard/
│   │   └── index.html      # Dashboard pós-login
│   └── news/
│       ├── list.html
│       └── detail.html
└── static/
    ├── css/
    │   └── style.css       # Estilos institucionais ETEC-IDEP
    └── js/
        └── logout.js       # Script de confirmação + POST logout
```

---

## Arquivos a Criar

### 1. `requirements.txt`
```
Django>=5.0
social-auth-app-django>=5.4
django-environ>=0.11
Pillow>=10.0
```

### 2. `pyproject.toml` — Ruff + Djlint
- Ruff: lint e format Python (target py311, line-length 88)
- Djlint: format HTML (profile django, indent 2)

### 3. `.env.example`
Variáveis: SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL,
SUAP_KEY, SUAP_SECRET, SUAP_URL=https://suap.ifrn.edu.br

### 4. `config/settings.py`
- django-environ para leitura do .env
- INSTALLED_APPS: social_django, apps.accounts, apps.dashboard, apps.news
- AUTHENTICATION_BACKENDS: SuapOAuth2 + ModelBackend
- SOCIAL_AUTH_SUAP_KEY / SUAP_SECRET via env
- AUTH_USER_MODEL = 'accounts.CustomUser'
- LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL

### 5. `apps/accounts/models.py`
CustomUser com campos extras: matricula, tipo_vinculo, foto (vindos do SUAP)

### 6. `apps/accounts/pipeline.py`
Pipeline social-auth para salvar dados do SUAP no CustomUser:
- matricula, tipo_vinculo, nome_usual, foto_url

### 7. Backend OAuth2 SUAP (`config/suap_backend.py`)
```python
from social_core.backends.oauth import BaseOAuth2

class SuapOAuth2(BaseOAuth2):
    name = "suap"
    BASE_URL = env("SUAP_URL", "https://suap.ifrn.edu.br")
    AUTHORIZATION_URL = f"{BASE_URL}/o/authorize/"
    ACCESS_TOKEN_URL = f"{BASE_URL}/o/token/"
    ACCESS_TOKEN_METHOD = "POST"
    REDIRECT_STATE = False
    DEFAULT_SCOPE = ["identificacao", "email", "documentos_pessoais"]

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(f"{self.BASE_URL}/api/eu/", headers={
            "Authorization": f"Bearer {access_token}"
        })

    def get_user_details(self, response):
        return {
            "username": response.get("identificacao"),
            "email": response.get("email"),
            "first_name": response.get("nome_usual"),
            "matricula": response.get("identificacao"),
            "tipo_vinculo": response.get("tipo_vinculo"),
        }
```

### 8. Templates
- `base.html`: navbar com logo ETEC-IDEP, links para dashboard/perfil/notícias, botão logout
- `accounts/login.html`: card centralizado com botão "Entrar com SUAP" (OAuth2)
- `accounts/profile.html`: foto, nome, matrícula, tipo de vínculo
- `dashboard/index.html`: boas-vindas + cards de acesso rápido
- `news/list.html` e `news/detail.html`

### 9. `static/js/logout.js`
```javascript
// Confirmação antes de logout + submissão via POST form
document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (confirm("Deseja realmente sair do sistema?")) {
        document.getElementById("logout-form").submit();
      }
    });
  }
});
```

### 10. `static/css/style.css`
Estilos institucionais com cores da ETEC-IDEP (paleta verde/branco)

---

## Configuração de Ferramentas

### Ruff (`pyproject.toml`)
```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]
```

### Djlint (`.djlintrc` ou `pyproject.toml`)
```toml
[tool.djlint]
profile = "django"
indent = 2
```

---

## Verificação (pós-implementação)
1. `pip install -r requirements.txt`
2. Copiar `.env.example` → `.env` e preencher SUAP_KEY/SUAP_SECRET
3. `python manage.py migrate`
4. `python manage.py runserver`
5. Acesso em http://localhost:8000 → botão "Entrar com SUAP"
6. `ruff check .` e `djlint templates/ --check` para validar formatação