"""
Django settings for the OnlyBall project.
"""

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

SITE_NAME = env('SITE_NAME', default='OnlyBall')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'rest_framework',
    'corsheaders',

    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'core.middleware.GeoBlockMiddleware',
    'core.middleware.SelfExclusionMiddleware',
]

ROOT_URLCONF = 'onlyball.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'onlyball.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

_database_url = env('DATABASE_URL', default='') or f'sqlite:///{BASE_DIR / "db.sqlite3"}'
DATABASES = {
    'default': env.db_url_config(_database_url)
}


AUTH_USER_MODEL = 'core.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
DRAW_TIME_ZONE = 'America/New_York'

USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']


# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'
# The manifest storage requires `collectstatic` to have been run, which
# isn't true in dev or under `manage.py test` (which forces DEBUG=False
# regardless of this file, so we can't key off DEBUG here). Opt into it
# explicitly for a real deployment via USE_MANIFEST_STATICFILES=True after
# running collectstatic.
USE_MANIFEST_STATICFILES = env.bool('USE_MANIFEST_STATICFILES', default=False)
STORAGES = {
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage' if USE_MANIFEST_STATICFILES
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/account/'
LOGOUT_REDIRECT_URL = '/'

# nginx terminates TLS in front of this app, so DEBUG=False in production
# implies HTTPS-only traffic reaches Django.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# --- Celery / Redis ---
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

from celery.schedules import crontab  # noqa: E402

# NOTE: Celery beat crontab entries are evaluated in CELERY_TIMEZONE (UTC).
# Because America/New_York's UTC offset changes with DST, we can't express
# "00:00 ET" as a single fixed UTC crontab. Instead these tasks run every
# minute and each one uses zoneinfo internally to check whether the actual
# ET boundary it cares about has just occurred, so it fires exactly once
# per real ET event regardless of DST (see core/tasks.py).
CELERY_BEAT_SCHEDULE = {
    'poll-pending-deposits-every-60s': {
        'task': 'core.tasks.poll_pending_deposits',
        'schedule': 60.0,
    },
    'process-approved-withdrawals-every-60s': {
        'task': 'core.tasks.process_approved_withdrawals',
        'schedule': 60.0,
    },
    'snapshot-tickets-tick': {
        'task': 'core.tasks.snapshot_tickets',
        'schedule': crontab(minute='*/1'),
    },
    'run-draw-tick': {
        'task': 'core.tasks.run_draw',
        'schedule': crontab(minute='*/1'),
    },
    'commit-next-seed-tick': {
        'task': 'core.tasks.commit_next_seed',
        'schedule': crontab(minute='*/1'),
    },
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_ALL_ORIGINS = DEBUG

# --- REST framework ---
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# --- Solana (beacon randomness only -- no funds, no keys; see services.beacon) ---
SOLANA_RPC_URL = env('SOLANA_RPC_URL', default='https://api.devnet.solana.com')

# --- NowPayments (USDT-TRC20 deposits, withdrawals, jackpot payouts) ---
NOWPAYMENTS_BASE_URL = env('NOWPAYMENTS_BASE_URL', default='https://api.nowpayments.io/v1')
NOWPAYMENTS_API_KEY = env('NOWPAYMENTS_API_KEY', default='')
NOWPAYMENTS_IPN_SECRET = env('NOWPAYMENTS_IPN_SECRET', default='')
NOWPAYMENTS_PAYOUT_EMAIL = env('NOWPAYMENTS_PAYOUT_EMAIL', default='')
NOWPAYMENTS_PAYOUT_PASSWORD = env('NOWPAYMENTS_PAYOUT_PASSWORD', default='')
NOWPAYMENTS_PAYOUT_IPN_URL = env('NOWPAYMENTS_PAYOUT_IPN_URL', default='')
PAY_CURRENCY = env('PAY_CURRENCY', default='usdttrc20')

# --- Economics (initial defaults; live values come from the Config singleton) ---
BALL_PRICE_USDT = env.float('BALL_PRICE_USDT', default=0.10)
TICKET_THRESHOLD = env.int('TICKET_THRESHOLD', default=100)
JACKPOT_BPS = env.int('JACKPOT_BPS', default=7000)
ROLLOVER_BPS = env.int('ROLLOVER_BPS', default=2000)
FEE_BPS = env.int('FEE_BPS', default=1000)
MIN_WITHDRAW = env.float('MIN_WITHDRAW', default=5.0)
KYC_THRESHOLD_USDT = env.float('KYC_THRESHOLD_USDT', default=100.0)

# --- Compliance ---
BLOCKED_COUNTRIES = env.list('BLOCKED_COUNTRIES', default=['US'])

# --- Email ---
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@onlyball.example')
