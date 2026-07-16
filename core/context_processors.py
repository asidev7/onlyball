from django.conf import settings


def site_settings(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'BLOCKED_COUNTRIES': settings.BLOCKED_COUNTRIES,
    }
