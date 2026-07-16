from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render


class GeoBlockMiddleware:
    """Blocks access from jurisdictions listed in settings.BLOCKED_COUNTRIES.

    Country is resolved from (in order): an explicit `X-Debug-Country` header
    (tests/local dev only), common CDN/proxy headers (Cloudflare, App Engine),
    or a GeoIP2 database if settings.GEOIP_PATH is configured. If no signal
    is available the request is allowed through -- this is a best-effort
    compliance layer, not a security boundary.
    """

    ALWAYS_ALLOWED_PREFIXES = ('/legal', '/static', '/admin')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        country = self.get_country_code(request)
        request.geo_country = country
        if country and country.upper() in settings.BLOCKED_COUNTRIES:
            if not any(request.path.startswith(p) for p in self.ALWAYS_ALLOWED_PREFIXES):
                return render(request, 'core/blocked.html', {'country': country}, status=451)
        return self.get_response(request)

    @staticmethod
    def get_country_code(request):
        if settings.DEBUG:
            header_country = request.headers.get('X-Debug-Country')
            if header_country:
                return header_country

        for header in ('HTTP_CF_IPCOUNTRY', 'HTTP_X_APPENGINE_COUNTRY'):
            val = request.META.get(header)
            if val:
                return val

        geoip_path = getattr(settings, 'GEOIP_PATH', None)
        if geoip_path:
            try:
                from django.contrib.gis.geoip2 import GeoIP2
                g = GeoIP2()
                ip = request.META.get('REMOTE_ADDR')
                return g.country_code(ip)
            except Exception:
                return None
        return None


class SelfExclusionMiddleware:
    """Blocks deposit/buy/withdraw actions while a user's self-exclusion
    period is active. Browsing (account, draws, fair) stays available so
    a self-excluded user can still see their history.
    """

    RESTRICTED_PREFIXES = ('/buy', '/deposit', '/withdraw')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and user.is_self_excluded:
            if any(request.path.startswith(p) for p in self.RESTRICTED_PREFIXES):
                messages.error(
                    request,
                    f'Your account is self-excluded until {user.self_excluded_until:%Y-%m-%d %H:%M} UTC.',
                )
                return redirect('account')
        return self.get_response(request)
