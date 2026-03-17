import os
from pathlib import Path
from datetime import timedelta

from decouple import Csv, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent
VALID_APP_ENVS = {"development", "homolog", "production"}
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

if APP_ENV not in VALID_APP_ENVS:
    APP_ENV = "development"


def env_default(development, homolog=None, production=None):
    values = {
        "development": development,
        "homolog": development if homolog is None else homolog,
        "production": (development if homolog is None else homolog) if production is None else production,
    }
    return values[APP_ENV]


if APP_ENV == "development":
    ENV_CANDIDATE_PATHS = [
        BASE_DIR / ".env.development",
        BASE_DIR / ".env",
        BASE_DIR / ".env.development.sample",
        BASE_DIR / ".env.sample",
    ]
else:
    ENV_CANDIDATE_PATHS = [
        BASE_DIR / f".env.{APP_ENV}",
        BASE_DIR / f".env.{APP_ENV}.sample",
        BASE_DIR / ".env",
        BASE_DIR / ".env.sample",
    ]
ENV_SOURCE_PATH = next((path for path in ENV_CANDIDATE_PATHS if path.exists()), BASE_DIR / ".env.sample")
ENV_REPOSITORY = RepositoryEnv(str(ENV_SOURCE_PATH))
ENV_DATA = ENV_REPOSITORY.data


def env(key, default=None, cast=None):
    value = os.getenv(key)

    if value is None:
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


def env_str(key, default=""):
    value = env(key, default=default)
    return default if value is None else str(value)


def env_bool(key, default=False):
    return bool(env(key, default=default, cast=bool))


def env_int(key, default=0):
    value = env(key, default=default, cast=int)

    if isinstance(value, int):
        return value

    if value is None or isinstance(value, (list, tuple)):
        return int(default)

    return int(str(value))


def env_csv(key, default=""):
    value = env(key, default=default, cast=Csv())

    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item]

    return [item.strip() for item in str(value).split(",") if item.strip()]


SECRET_KEY = env_str("SECRET_KEY", default="django-insecure-troque-isso-depois")

APP_ENVIRONMENT = APP_ENV

DEBUG = env_bool("DEBUG", default=env_default(True, homolog=False, production=False))
DJANGO_TEMPLATE_UI_ENABLED = env_bool("DJANGO_TEMPLATE_UI_ENABLED", default=True)

ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS", default=env_default("127.0.0.1,localhost", homolog="", production=""))

CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS", default=env_default("http://127.0.0.1:5173,http://localhost:5173", homolog="", production=""))
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", default=True)
CSRF_TRUSTED_ORIGINS = env_csv("CSRF_TRUSTED_ORIGINS", default="")


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
    "apps.setores",
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
    "apps.notificacoes",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'config.middleware.BlockDjangoTemplateUIMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.ForcePasswordChangeMiddleware',
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
        "ENGINE": env("DATABASE_ENGINE", default=env_default("django.db.backends.sqlite3", homolog="django.db.backends.postgresql", production="django.db.backends.postgresql")),
        "NAME": env_str("DATABASE_NAME", default=env_default(str(BASE_DIR / "db.sqlite3"), homolog="suap_idep_homolog", production="suap_idep")),
        "USER": env_str("DATABASE_USER", default=""),
        "PASSWORD": env_str("DATABASE_PASSWORD", default=""),
        "HOST": env_str("DATABASE_HOST", default=""),
        "PORT": env_str("DATABASE_PORT", default=""),
        "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", default=env_default(0, homolog=60, production=300)),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = env_str("LANGUAGE_CODE", default="pt-br")

TIME_ZONE = env_str("TIME_ZONE", default="America/Cuiaba")

USE_I18N = env_bool("USE_I18N", default=True)

USE_TZ = env_bool("USE_TZ", default=True)


TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]


STATIC_URL = env_str("STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(env_str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))

MEDIA_URL = env_str("MEDIA_URL", default="/media/")
MEDIA_ROOT = Path(env_str("MEDIA_ROOT", default=str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = env_str("LOGIN_URL", default="accounts:login")
LOGIN_REDIRECT_URL = env_str("LOGIN_REDIRECT_URL", default="dashboard:index")
LOGOUT_REDIRECT_URL = env_str("LOGOUT_REDIRECT_URL", default="accounts:login")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=env_default(False, homolog=False, production=True))
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=env_default(False, homolog=False, production=True))
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=env_default(False, homolog=False, production=True))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1)),
    "ROTATE_REFRESH_TOKENS": env_bool("JWT_ROTATE_REFRESH_TOKENS", default=True),
    "BLACKLIST_AFTER_ROTATION": env_bool("JWT_BLACKLIST_AFTER_ROTATION", default=True),
    "UPDATE_LAST_LOGIN": env_bool("JWT_UPDATE_LAST_LOGIN", default=True),
    "ALGORITHM": env_str("JWT_ALGORITHM", default="HS256"),
    "SIGNING_KEY": env_str("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": tuple(env_csv("JWT_AUTH_HEADER_TYPES", default="Bearer")),
}

MOODLE_BASE_URL = env_str("MOODLE_BASE_URL", default=env_str("MOODLE_API_BASE_URL", default=""))
MOODLE_WS_TOKEN = env_str("MOODLE_WS_TOKEN", default=env_str("MOODLE_API_TOKEN", default=""))
MOODLE_REST_FORMAT = env_str("MOODLE_REST_FORMAT", default=env_str("MOODLE_API_WS_FORMAT", default="json"))
MOODLE_TIMEOUT = env_int("MOODLE_TIMEOUT", default=env_int("MOODLE_API_TIMEOUT", default=30))
MOODLE_VERIFY_SSL = env_bool(
    "MOODLE_VERIFY_SSL",
    default=env_bool("MOODLE_API_VERIFY_SSL", default=env_default(False, homolog=True, production=True)),
)
MOODLE_REST_PATH = env_str("MOODLE_REST_PATH", default=env_str("MOODLE_API_REST_PATH", default="webservice/rest/server.php"))

MOODLE_API_BASE_URL = MOODLE_BASE_URL
MOODLE_API_REST_PATH = MOODLE_REST_PATH
MOODLE_API_TOKEN = MOODLE_WS_TOKEN
MOODLE_API_TIMEOUT = MOODLE_TIMEOUT
MOODLE_API_VERIFY_SSL = MOODLE_VERIFY_SSL
MOODLE_API_WS_FORMAT = MOODLE_REST_FORMAT

INITIAL_ADMIN_CPF = env_str("INITIAL_ADMIN_CPF", default="")
INITIAL_ADMIN_PASSWORD = env_str("INITIAL_ADMIN_PASSWORD", default="admin")
INITIAL_ADMIN_FIRST_NAME = env_str("INITIAL_ADMIN_FIRST_NAME", default="Administrador")
INITIAL_ADMIN_LAST_NAME = env_str("INITIAL_ADMIN_LAST_NAME", default="Inicial")
