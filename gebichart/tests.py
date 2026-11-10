import hashlib
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class WorkspaceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('gestor', password='test-password')

    def test_anonymous_home_requires_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, '/acceso/?next=/', fetch_redirect_response=False)

    def test_login_home_logout(self):
        response = self.client.post(reverse('login'), {
            'username': 'gestor', 'password': 'test-password',
        })
        self.assertRedirects(response, reverse('home'))
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'El patrimonio, en un mismo lugar.')
        self.assertNotContains(response, 'Administrar usuarios')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('home')).status_code, 302)

    def test_regular_user_cannot_access_admin(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)

    def test_login_does_not_redirect_to_external_site(self):
        response = self.client.post(reverse('login'), {
            'username': 'gestor', 'password': 'test-password',
            'next': 'https://example.org/',
        })
        self.assertRedirects(response, reverse('home'))

    def test_staff_sees_admin_link(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('home')), 'Administrar usuarios')
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_all_original_assets_resolve_without_changes(self):
        original = settings.BASE_DIR / 'GEBICHART_INTEGRACION_CODEX/marca_original/static'
        for source in original.rglob('*'):
            if source.is_file():
                with self.subTest(asset=source.name):
                    resolved = finders.find(source.relative_to(original).as_posix())
                    self.assertIsNotNone(resolved)
                    self.assertEqual(hashlib.sha256(Path(resolved).read_bytes()).digest(),
                                     hashlib.sha256(source.read_bytes()).digest())
