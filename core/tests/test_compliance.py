import datetime

from django.test import TestCase, override_settings
from django.utils import timezone

from core.forms import EmailSignupForm
from core.models import User


@override_settings(DEBUG=True)  # the X-Debug-Country test header is only honored in debug mode
class GeoBlockMiddlewareTests(TestCase):
    def test_blocked_country_gets_451(self):
        response = self.client.get('/', headers={'X-Debug-Country': 'US'})
        self.assertEqual(response.status_code, 451)

    def test_non_blocked_country_passes_through(self):
        response = self.client.get('/', headers={'X-Debug-Country': 'FR'})
        self.assertEqual(response.status_code, 200)

    def test_legal_page_always_reachable_even_when_blocked(self):
        response = self.client.get('/legal/', headers={'X-Debug-Country': 'US'})
        self.assertEqual(response.status_code, 200)

    def test_no_country_signal_passes_through(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class SelfExclusionMiddlewareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='pass12345')
        self.user.self_excluded_until = timezone.now() + datetime.timedelta(days=7)
        self.user.save()

    def test_self_excluded_user_blocked_from_buy(self):
        self.client.force_login(self.user)
        response = self.client.get('/buy/', follow=True)
        self.assertRedirects(response, '/account/')

    def test_self_excluded_user_blocked_from_deposit(self):
        self.client.force_login(self.user)
        response = self.client.get('/deposit/', follow=True)
        self.assertRedirects(response, '/account/')

    def test_self_excluded_user_can_still_view_account(self):
        self.client.force_login(self.user)
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)

    def test_expired_self_exclusion_no_longer_blocks(self):
        self.user.self_excluded_until = timezone.now() - datetime.timedelta(days=1)
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get('/buy/')
        self.assertEqual(response.status_code, 200)


class AgeGateTests(TestCase):
    def test_under_18_signup_rejected(self):
        too_young = (timezone.localdate() - datetime.timedelta(days=17 * 365)).isoformat()
        form = EmailSignupForm(data={
            'email': 'kid@example.com', 'birth_date': too_young,
            'password1': 'somepass123', 'password2': 'somepass123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)

    def test_18_or_older_signup_accepted(self):
        adult = (timezone.localdate() - datetime.timedelta(days=19 * 365)).isoformat()
        form = EmailSignupForm(data={
            'email': 'adult@example.com', 'birth_date': adult,
            'password1': 'somepass123', 'password2': 'somepass123',
        })
        self.assertTrue(form.is_valid())
