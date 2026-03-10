from pathlib import Path
from datetime import timedelta

from decouple import Csv, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
ENV_SAMPLE_PATH = BASE_DIR / ".env.sample"
ENV_SOURCE_PATH = ENV_PATH if ENV_PATH.exists() else ENV_SAMPLE_PATH
ENV_REPOSITORY = RepositoryEnv(str(ENV_SOURCE_PATH))
ENV_DATA = ENV_REPOSITORY.data


def env(key, default=None, cast=None):
    value = ENV_DATA.get(key, default)

    if value is None or cast is None:
        return value

    if cast is bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    if cast is int:
        if isinstance(value, int):
            return value
        return int(value)

    if isinstance(cast, Csv):
        return cast(value)

    return cast(value)


SECRET_KEY = env("SECRET_KEY", default="django-insecure-troque-isso-depois")

DEBUG = env("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="", cast=Csv())

CORS_ALLOWED_ORIGINS = [origin for origin in env("CORS_ALLOWED_ORIGINS", default="", cast=Csv()) if origin]
CORS_ALLOW_CREDENTIALS = env("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',

    "apps.core",
    "apps.dashboard",
    "apps.cursos",
    "apps.integracao_moodle",
    "apps.matriculas",
    "apps.turmas",
    "apps.unidades",
    "apps.usuarios",
    "apps.accounts",
    "apps.access",
    "apps.notas",
    "apps.frequencia",
    "apps.agenda",
    "apps.processos",
    "apps.arquivo",
    "apps.documentos",
    "apps.auditoria",
    "apps.inscricoes",
    "apps.estagio",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.app_info",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": env("DATABASE_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("DATABASE_NAME", default=str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = env("LANGUAGE_CODE", default="pt-br")

TIME_ZONE = env("TIME_ZONE", default="America/Cuiaba")

USE_I18N = env("USE_I18N", default=True, cast=bool)

USE_TZ = env("USE_TZ", default=True, cast=bool)


TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]


STATIC_URL = env("STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = env("LOGIN_URL", default="accounts:login")
LOGIN_REDIRECT_URL = env("LOGIN_REDIRECT_URL", default="dashboard:index")
LOGOUT_REDIRECT_URL = env("LOGOUT_REDIRECT_URL", default="accounts:login")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1, cast=int)),
    "ROTATE_REFRESH_TOKENS": env("JWT_ROTATE_REFRESH_TOKENS", default=True, cast=bool),
    "BLACKLIST_AFTER_ROTATION": env("JWT_BLACKLIST_AFTER_ROTATION", default=True, cast=bool),
    "UPDATE_LAST_LOGIN": env("JWT_UPDATE_LAST_LOGIN", default=True, cast=bool),
    "ALGORITHM": env("JWT_ALGORITHM", default="HS256"),
    "AUTH_HEADER_TYPES": tuple(env("JWT_AUTH_HEADER_TYPES", default="Bearer", cast=Csv())),
}
