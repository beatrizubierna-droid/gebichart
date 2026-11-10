from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import ObraForm
from .models import Obra


class InventarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.lector = users.objects.create_user('consulta')
        cls.editor = users.objects.create_user('edicion')
        cls.sin_acceso = users.objects.create_user('sin-acceso', is_staff=True)
        call_command('crear_roles', stdout=StringIO())
        cls.lector.groups.add(Group.objects.get(name='Consulta inventario'))
        cls.editor.groups.add(Group.objects.get(name='Gestión inventario'))
        cls.obra = Obra.objects.create(
            codigo='GCH-001', titulo='Paisaje de prueba', autoria='Autoría de prueba',
            tipo='pintura', ubicacion='Sala de pruebas', conservacion='bueno',
        )

    def datos(self, **overrides):
        return {
            'codigo': 'gch-002', 'titulo': 'Otra obra', 'tipo': 'escultura',
            'conservacion': 'sin_evaluar', **overrides,
        }

    def test_anonymous_cannot_read_or_modify_inventory(self):
        for url in [reverse('obra_list'), self.obra.get_absolute_url(),
                    reverse('obra_create'), reverse('obra_update', args=[self.obra.pk])]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url, self.datos()).status_code, 302)
        self.assertEqual(Obra.objects.count(), 1)

    def test_staff_without_model_permissions_is_denied(self):
        self.client.force_login(self.sin_acceso)
        for url in [reverse('obra_list'), self.obra.get_absolute_url(),
                    reverse('obra_create'), reverse('obra_update', args=[self.obra.pk])]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, self.datos()).status_code, 403)
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Abrir inventario')
        self.assertEqual(Obra.objects.count(), 1)

    def test_readonly_role_can_read_but_cannot_write(self):
        self.client.force_login(self.lector)
        self.assertContains(self.client.get(reverse('obra_list')), self.obra.titulo)
        self.assertContains(self.client.get(self.obra.get_absolute_url()), self.obra.codigo)
        response = self.client.get(reverse('obra_list'))
        self.assertNotContains(response, 'Añadir obra')
        for url in [reverse('obra_create'), reverse('obra_update', args=[self.obra.pk])]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, self.datos()).status_code, 403)
        self.obra.refresh_from_db()
        self.assertEqual(self.obra.titulo, 'Paisaje de prueba')
        self.assertEqual(Obra.objects.count(), 1)

    def test_editor_can_create_and_update_without_staff(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(reverse('obra_create')).status_code, 200)
        response = self.client.post(reverse('obra_create'), self.datos())
        obra = Obra.objects.get(codigo='GCH-002')
        self.assertRedirects(response, obra.get_absolute_url(), fetch_redirect_response=False)
        self.assertContains(self.client.get(obra.get_absolute_url()), 'guardada correctamente')
        self.assertEqual(self.client.get(reverse('obra_update', args=[obra.pk])).status_code, 200)
        response = self.client.post(reverse('obra_update', args=[obra.pk]),
                                    self.datos(titulo='Título revisado'))
        self.assertRedirects(response, obra.get_absolute_url())
        obra.refresh_from_db()
        self.assertEqual(obra.titulo, 'Título revisado')
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)

    def test_add_permission_does_not_grant_edit(self):
        self.lector.user_permissions.add(Permission.objects.get(
            content_type__app_label='gebichart', codename='add_obra',
        ))
        self.client.force_login(self.lector)
        self.assertEqual(self.client.get(reverse('obra_create')).status_code, 200)
        self.assertEqual(self.client.post(reverse('obra_update', args=[self.obra.pk]),
                                         self.datos()).status_code, 403)

    def test_duplicate_normalized_code_is_rejected(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('obra_create'), self.datos(codigo=' gch-001 '))
        self.assertEqual(response.status_code, 200)
        self.assertIn('codigo', response.context['form'].errors)
        self.assertContains(response, 'No se ha guardado la obra.')
        self.assertEqual(Obra.objects.count(), 1)

    def test_invalid_submission_is_not_saved_and_preserves_values(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('obra_create'), self.datos(
            codigo='con espacios', titulo='', tipo='invalido', conservacion='invalido',
            autoria='Valor que debe conservarse',
        ))
        self.assertEqual(response.status_code, 200)
        for field in ('codigo', 'titulo', 'tipo', 'conservacion'):
            self.assertIn(field, response.context['form'].errors)
        self.assertContains(response, 'Valor que debe conservarse')
        self.assertEqual(Obra.objects.count(), 1)

    def test_edit_form_uses_same_unique_code_validation(self):
        form = ObraForm(self.datos(codigo=' gch-001 '), instance=self.obra)
        self.assertTrue(form.is_valid(), form.errors)
        other = Obra.objects.create(codigo='GCH-003', titulo='Otra', tipo='dibujo')
        form = ObraForm(self.datos(codigo='gch-001'), instance=other)
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)

    def test_search_and_filters(self):
        Obra.objects.create(codigo='GCH-002', titulo='Escultura de prueba', tipo='escultura')
        self.client.force_login(self.lector)
        for query in ('GCH-001', 'Paisaje', 'Autoría de prueba', 'Sala de pruebas'):
            response = self.client.get(reverse('obra_list'), {'q': query})
            self.assertContains(response, 'Paisaje de prueba')
            self.assertNotContains(response, 'Escultura de prueba')
        response = self.client.get(reverse('obra_list'), {
            'q': 'prueba', 'tipo': 'escultura', 'conservacion': 'sin_evaluar',
        })
        self.assertContains(response, 'Escultura de prueba')
        self.assertNotContains(response, 'Paisaje de prueba')
        self.assertContains(self.client.get(reverse('obra_list'), {'q': 'inexistente'}),
                            'No hay obras que coincidan')

    def test_pagination_keeps_search_and_filters(self):
        Obra.objects.bulk_create([
            Obra(codigo=f'P-{i:03}', titulo=f'Obra paginada {i}', tipo='pintura')
            for i in range(23)
        ])
        self.client.force_login(self.lector)
        response = self.client.get(reverse('obra_list'), {'q': 'paginada', 'tipo': 'pintura'})
        self.assertEqual(len(response.context['obras']), 20)
        self.assertContains(response, 'q=paginada&amp;tipo=pintura&amp;page=2')
        response = self.client.get(reverse('obra_list'), {
            'q': 'paginada', 'tipo': 'pintura', 'page': 2,
        })
        self.assertEqual(len(response.context['obras']), 3)

    def test_empty_inventory_and_missing_record(self):
        Obra.objects.all().delete()
        self.client.force_login(self.editor)
        self.assertContains(self.client.get(reverse('obra_list')), 'Registrar la primera obra')
        self.assertEqual(self.client.get(reverse('obra_detail', args=[9999])).status_code, 404)

    def test_user_content_is_escaped(self):
        self.obra.titulo = '<script>alert(1)</script>'
        self.obra.descripcion = '<img src=x onerror=alert(1)>'
        self.obra.save()
        self.client.force_login(self.lector)
        response = self.client.get(self.obra.get_absolute_url())
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<img src=x')

    @override_settings(CSRF_TRUSTED_ORIGINS=['https://localhost:8000'])
    def test_csrf_blocks_missing_token_and_allows_trusted_local_origin(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        self.assertEqual(client.post(reverse('obra_create'), self.datos()).status_code, 403)
        client.get(reverse('obra_create'))
        token = client.cookies['csrftoken'].value
        response = client.post(reverse('obra_create'), {
            **self.datos(), 'csrfmiddlewaretoken': token,
        }, HTTP_ORIGIN='https://localhost:8000')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.post(reverse('obra_create'), {
            **self.datos(codigo='GCH-003'), 'csrfmiddlewaretoken': token,
        }, HTTP_ORIGIN='https://untrusted.example').status_code, 403)
        self.assertEqual(Obra.objects.count(), 2)

    def test_role_command_is_idempotent_and_does_not_assign_users(self):
        call_command('crear_roles', stdout=StringIO())
        call_command('crear_roles', stdout=StringIO())
        self.assertEqual(Group.objects.get(name='Consulta inventario').permissions.count(), 4)
        self.assertEqual(Group.objects.get(name='Gestión inventario').permissions.count(), 12)
        self.assertFalse(self.sin_acceso.groups.exists())
        self.assertFalse(self.editor.has_perm('gebichart.delete_obra'))

    def test_admin_uses_inventory_form_and_model_permissions(self):
        admin = get_user_model().objects.create_superuser('admin-prueba')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('admin:gebichart_obra_add')).status_code, 200)
        response = self.client.post(reverse('admin:gebichart_obra_add'), self.datos())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Obra.objects.filter(codigo='GCH-002').exists())
        self.assertEqual(self.client.get(reverse('admin:gebichart_obra_change',
                                                 args=[self.obra.pk])).status_code, 200)
        self.client.force_login(self.sin_acceso)
        self.assertEqual(self.client.get(reverse('admin:gebichart_obra_changelist')).status_code,
                         403)
