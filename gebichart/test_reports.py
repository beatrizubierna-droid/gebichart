from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Edificio, Obra, Planta, Ubicacion


class ReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('crear_roles', stdout=StringIO())
        users = get_user_model()
        cls.lector = users.objects.create_user('lector-impresion')
        cls.lector.groups.add(Group.objects.get(name='Consulta inventario'))
        cls.sin_acceso = users.objects.create_user('staff-sin-permisos', is_staff=True)
        cls.usuarios_lector = users.objects.create_user('auditor-usuarios')
        cls.usuarios_lector.user_permissions.add(Permission.objects.get(
            content_type__app_label='auth', codename='view_user',
        ))
        cls.edificio = Edificio.objects.create(codigo='IMP-01', nombre='Edificio impresión')
        cls.planta = Planta.objects.create(edificio=cls.edificio, nombre='Planta baja')
        cls.espacio = Ubicacion.objects.create(planta=cls.planta, nombre='Sala impresión')
        cls.otra = Ubicacion.objects.create(planta=cls.planta, nombre='Otra sala')
        Obra.objects.bulk_create([
            Obra(codigo=f'IMP-{i:03}', titulo=f'Obra impresa {i}', tipo='pintura',
                 conservacion='bueno', espacio=cls.espacio) for i in range(31)
        ])
        cls.excluida = Obra.objects.create(codigo='EXCLUIDA', titulo='Obra fuera del filtro',
                                         tipo='escultura', espacio=cls.otra)
        cls.grupo = Group.objects.create(name='Grupo impresión de prueba')
        for i in range(30):
            user = users.objects.create_user(f'imp-user-{i:02}', first_name=f'Nombre {i}',
                                             last_name='Prueba', email=f'prueba{i}@example.test',
                                             password='test-password', is_active=i % 2 == 0)
            user.groups.add(cls.grupo)
        # A user in several matching groups must appear only once.
        Group.objects.create(name='Grupo impresión extra').user_set.add(user)

    def urls(self):
        return [reverse('obras_print'), reverse('catalogo_print'), reverse('usuarios_print'),
                reverse('usuarios_list'), reverse('ubicacion_obras_print', args=[self.espacio.pk])]

    def test_anonymous_and_unprivileged_staff_are_denied(self):
        for url in self.urls():
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.sin_acceso)
        for url in self.urls():
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_inventory_roles_cannot_read_or_print_users(self):
        self.client.force_login(self.lector)
        self.assertEqual(self.client.get(reverse('usuarios_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('usuarios_print')).status_code, 403)
        self.assertNotContains(self.client.get(reverse('home')), 'href="/usuarios/"')
        self.assertEqual(self.client.get(reverse('obras_print')).status_code, 200)
        self.assertEqual(self.client.get(reverse('catalogo_print')).status_code, 200)

    def test_artwork_print_contains_all_filtered_pages(self):
        self.client.force_login(self.lector)
        filters = {'q': 'Obra impresa', 'tipo': 'pintura', 'conservacion': 'bueno',
                   'edificio': self.edificio.pk, 'page': 2}
        response = self.client.get(reverse('obras_print'), filters)
        self.assertEqual(len(response.context['obras']), 31)
        self.assertEqual(response.context['report_total'], 31)
        self.assertIsNone(response.context['paginator'])
        self.assertContains(response, 'IMP-000')
        self.assertContains(response, 'IMP-030')
        self.assertNotContains(response, self.excluida.titulo)
        self.assertContains(response, 'Edificio impresión')
        self.assertContains(response, 'Bueno')
        self.assertNotIn('page=', response.context['return_url'])

    def test_filtered_links_preserve_query_and_do_not_use_post(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('obra_list'), {'q': 'texto & otro', 'tipo': 'pintura'})
        self.assertContains(response, '/inventario/imprimir/?q=texto+%26+otro&amp;tipo=pintura')
        response = self.client.get(reverse('catalogo'), {'q': 'Sala impresión',
                                                       'edificio': self.edificio.pk})
        self.assertContains(response, 'q=Sala%20impresi%C3%B3n&amp;edificio=')
        self.assertEqual(self.client.post(reverse('obras_print'), {}).status_code, 405)

    def test_catalog_print_covers_all_buildings_and_empty_levels(self):
        Edificio.objects.bulk_create([Edificio(codigo=f'VACIO-{i}', nombre=f'Edificio vacío {i}')
                                     for i in range(12)])
        Planta.objects.create(edificio=self.edificio, nombre='Planta sin salas', orden=1)
        self.client.force_login(self.lector)
        response = self.client.get(reverse('catalogo_print'), {'page': 2})
        self.assertEqual(response.context['report_total'], 13)
        self.assertEqual(response.context['report_plantas'], 2)
        self.assertEqual(response.context['report_ubicaciones'], 2)
        self.assertContains(response, 'VACIO-11')
        self.assertContains(response, 'Sin plantas')
        self.assertContains(response, 'Sin ubicaciones')
        response = self.client.get(reverse('catalogo_print'), {'q': 'Sala impresión',
                                                             'edificio': self.edificio.pk})
        self.assertEqual(response.context['report_total'], 1)
        self.assertNotContains(response, 'VACIO-11')

    def test_location_print_scopes_works_and_includes_every_page(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('ubicacion_obras_print', args=[self.espacio.pk]),
                                   {'page': 2, 'q': 'ignored'})
        self.assertEqual(response.context['report_total'], 31)
        self.assertContains(response, 'IMP-030')
        self.assertNotContains(response, self.excluida.titulo)
        self.assertEqual(response.context['return_url'], self.espacio.get_absolute_url())
        self.assertEqual(self.client.get(reverse('ubicacion_obras_print', args=[999999])).status_code,
                         404)

    def test_catalog_user_without_inventory_access_does_not_get_work_counts(self):
        self.sin_acceso.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='gebichart', codename__in=(
                'view_edificio', 'view_planta', 'view_ubicacion',
            ),
        ))
        self.client.force_login(self.sin_acceso)
        response = self.client.get(reverse('catalogo_print'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<th scope="col">Obras</th>')
        self.assertEqual(self.client.get(reverse('ubicacion_obras_print',
                                                 args=[self.espacio.pk])).status_code, 403)

    def test_users_read_permission_is_independent_of_staff_status(self):
        self.client.force_login(self.usuarios_lector)
        response = self.client.get(reverse('usuarios_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/usuarios/"')
        self.assertEqual(self.client.get(reverse('usuarios_print')).status_code, 200)
        self.assertEqual(self.client.get(reverse('obras_print')).status_code, 403)

    def test_user_filters_print_all_results_and_exclude_password_data(self):
        self.client.force_login(self.usuarios_lector)
        filters = {'q': 'imp-user-', 'grupo': self.grupo.pk, 'activo': '1'}
        response = self.client.get(reverse('usuarios_print'), filters)
        self.assertEqual(response.context['report_total'], 15)
        self.assertContains(response, 'imp-user-00')
        self.assertContains(response, 'imp-user-28')
        self.assertNotContains(response, 'imp-user-29')
        self.assertContains(response, 'prueba0@example.test')
        self.assertContains(response, 'Grupo impresión de prueba')
        user = get_user_model().objects.get(username='imp-user-00')
        self.assertNotContains(response, user.password)
        self.assertNotContains(response, 'test-password')
        response = self.client.get(reverse('usuarios_print'), {'q': 'imp-user-', 'page': 2})
        self.assertEqual(response.context['report_total'], 30)
        self.assertContains(response, 'imp-user-00')
        self.assertContains(response, 'imp-user-29')
        response = self.client.get(reverse('usuarios_print'), {'q': 'Grupo impresión'})
        self.assertEqual(response.context['report_total'], 30)

    def test_invalid_user_filters_and_empty_results(self):
        self.client.force_login(self.usuarios_lector)
        for filters in ({'grupo': 'invalid'}, {'activo': 'invalid'}, {'q': 'no-existe'}):
            response = self.client.get(reverse('usuarios_print'), filters)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['report_total'], 0)
            self.assertContains(response, 'No hay usuarios que coincidan')
        self.client.force_login(self.lector)
        response = self.client.get(reverse('obras_print'), {'q': 'no-existe'})
        self.assertContains(response, 'No hay obras que coincidan')

    def test_reports_have_private_cache_and_print_controls(self):
        self.client.force_login(self.lector)
        for url in (reverse('obras_print'), reverse('catalogo_print')):
            response = self.client.get(url)
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
            self.assertContains(response, 'data-print')
            self.assertContains(response, 'gebichart/css/print.css')
            self.assertContains(response, 'gebichart/js/print.js')
            self.assertContains(response, 'hora de Madrid')
        self.client.force_login(self.usuarios_lector)
        self.assertEqual(self.client.get(reverse('usuarios_print'))['Cache-Control'],
                         'private, no-store')

    def test_filter_values_and_user_data_are_escaped(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('obras_print'), {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        get_user_model().objects.filter(pk=self.usuarios_lector.pk).update(first_name='<b>unsafe</b>')
        self.client.force_login(self.usuarios_lector)
        response = self.client.get(reverse('usuarios_print'))
        self.assertNotContains(response, '<b>unsafe</b>')
        self.assertContains(response, '&lt;b&gt;unsafe&lt;/b&gt;')

    def test_admin_user_list_links_to_printable_listing(self):
        admin = get_user_model().objects.create_superuser('admin-impresion')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:auth_user_changelist'))
        self.assertContains(response, 'Listado e impresión de usuarios')
        self.assertContains(response, reverse('usuarios_list'))
