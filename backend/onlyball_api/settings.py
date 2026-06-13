"""Django settings for the OnlyBall API.

Lightweight DRF service that indexes on-chain lottery activity and keeps the
off-chain account/referral ledger. Configuration is read from environment
variables (see .env.example); a tiny loader below reads a local .env file so
no extra dependency is required.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE lines) — avoids a python-dotenv dep."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


SECRET_KEY = env("SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = env("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "*").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "lottery",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "onlyball_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "onlyball_api.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in env("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

# --- OnlyBall / TRON configuration ---
NETWORK = env("NETWORK", "mainnet")
TRON_HOST = (
    "https://api.shasta.trongrid.io"
    if NETWORK == "shasta"
    else "https://api.trongrid.io"
)
TREASURY_ADDRESS = env("TREASURY_ADDRESS", "TUeUpadvBCc6U3n3rd4BvNvw8fC7B9DXvT")
# Deployed OnlyBall lottery contract (empty until deployed). When set, tickets
# are bought through the contract and verified as calls to it.
ONLYBALL_ADDRESS = env("ONLYBALL_ADDRESS", "")
FUDSX_ADDRESS = env("FUDSX_ADDRESS", "TPF44Br5XkJw6snvo3URN4CT7UALJZggtG")
USDT_ADDRESS = env("USDT_ADDRESS", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
TRONGRID_API_KEY = env("TRONGRID_API_KEY", "")

FUDSX_DECIMALS = int(env("FUDSX_DECIMALS", "18"))
TICKET_PRICE_FUDSX = int(env("TICKET_PRICE_FUDSX", "200"))
REFERRAL_REWARD_FUDSX = int(env("REFERRAL_REWARD_FUDSX", "5"))
