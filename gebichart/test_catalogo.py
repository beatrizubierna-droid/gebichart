from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from .forms import EdificioForm, PlantaForm, UbicacionForm
from .models import Edificio, FotoObra, Obra, Planta, Ubicacion


class CatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('crear_roles', stdout=StringIO())
        users = get_user_model()
        cls.lector = users.objects.create_user('catalogo-lector')
        cls.editor = users.objects.create_user('catalogo-editor')
        cls.sin_acceso = users.objects.create_user('catalogo-staff', is_staff=True)
        cls.lector.groups.add(Group.objects.get(name='Consulta inventario'))
        cls.editor.groups.add(Group.objects.get(name='Gestión inventario'))
        cls.edificio = Edificio.objects.create(codigo='EDI-01', nombre='Edificio de prueba')
        cls.planta = Planta.objects.create(edificio=cls.edificio, nombre='Planta baja')
        cls.espacio = Ubicacion.objects.create(planta=cls.planta, nombre='Sala de prueba')
        cls.otra_planta = Planta.objects.create(edificio=cls.edificio, nombre='Primera planta', orden=1)
        cls.obra = Obra.objects.create(codigo='CAT-01', titulo='Obra ubicada', tipo='pintura',
                                      espacio=cls.espacio)
        cls.legacy = Obra.objects.create(codigo='CAT-02', titulo='Obra anterior', tipo='pintura',
                                        ubicacion='Referencia antigua exacta')

    def urls_escritura(self):
        return [reverse('edificio_create'), reverse('edificio_update', args=[self.edificio.pk]),
                reverse('planta_create'), reverse('planta_update', args=[self.planta.pk]),
                reverse('ubicacion_create'), reverse('ubicacion_update', args=[self.espacio.pk])]

    def setUp(self):
        self.client.force_login(self.editor)

    def test_authentication_and_permissions_on_every_route(self):
        reads = [reverse('catalogo'), self.espacio.get_absolute_url()]
        self.client.logout()
        for url in reads + self.urls_escritura():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url, {}).status_code, 302)
        self.client.force_login(self.sin_acceso)
        for url in reads + self.urls_escritura():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.client.force_login(self.lector)
        for url in reads:
            self.assertEqual(self.client.get(url).status_code, 200)
        for url in self.urls_escritura():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_create_entire_hierarchy(self):
        response = self.client.post(reverse('edificio_create'), {
            'codigo': 'edi-02', 'nombre': 'Nuevo edificio', 'direccion': 'Dirección de prueba',
        })
        edificio = Edificio.objects.get(codigo='EDI-02')
        self.assertRedirects(response, edificio.get_absolute_url())
        response = self.client.post(reverse('planta_create'), {
            'edificio': edificio.pk, 'nombre': 'Baja', 'orden': 0,
        })
        planta = edificio.plantas.get()
        self.assertRedirects(response, planta.get_absolute_url())
        response = self.client.post(reverse('ubicacion_create'), {
            'planta': planta.pk, 'nombre': 'Depósito', 'descripcion': 'Descripción de prueba',
        })
        espacio = planta.ubicaciones.get()
        self.assertRedirects(response, espacio.get_absolute_url())
        for url in self.urls_escritura():
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_parent_preselection_and_artwork_preselection(self):
        response = self.client.get(reverse('planta_create'), {'edificio': self.edificio.pk})
        self.assertEqual(int(response.context['form']['edificio'].value()), self.edificio.pk)
        response = self.client.get(reverse('ubicacion_create'), {'planta': self.planta.pk})
        self.assertEqual(int(response.context['form']['planta'].value()), self.planta.pk)
        response = self.client.get(reverse('obra_create'), {'espacio': self.espacio.pk})
        self.assertEqual(int(response.context['form']['espacio'].value()), self.espacio.pk)
        self.assertEqual(self.client.get(reverse('planta_create'), {'edificio': 'bad'}).status_code, 200)

    def test_duplicates_are_scoped_to_parent(self):
        form = EdificioForm({'codigo': 'edi-01', 'nombre': 'Duplicado'})
        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)
        form = PlantaForm({'edificio': self.edificio.pk, 'nombre': self.planta.nombre, 'orden': 0})
        self.assertFalse(form.is_valid())
        other = Edificio.objects.create(codigo='OTRO', nombre='Otro')
        self.assertTrue(PlantaForm({'edificio': other.pk, 'nombre': self.planta.nombre,
                                   'orden': 0}).is_valid())
        self.assertFalse(UbicacionForm({'planta': self.planta.pk,
                                       'nombre': self.espacio.nombre}).is_valid())
        self.assertTrue(UbicacionForm({'planta': self.otra_planta.pk,
                                      'nombre': self.espacio.nombre}).is_valid())

    def test_invalid_parents_and_required_values_are_rejected(self):
        response = self.client.post(reverse('planta_create'), {'edificio': 999999, 'nombre': '',
                                                              'orden': 'bad'})
        self.assertEqual(response.status_code, 200)
        for field in ('edificio', 'nombre', 'orden'):
            self.assertIn(field, response.context['form'].errors)
        response = self.client.post(reverse('ubicacion_create'), {'planta': 999999, 'nombre': 'Sala'})
        self.assertIn('planta', response.context['form'].errors)
        self.assertEqual(Ubicacion.objects.count(), 1)

    def test_edits_keep_parent_links_stable_even_with_tampered_post(self):
        other = Edificio.objects.create(codigo='OTRO', nombre='Otro edificio')
        self.client.post(reverse('planta_update', args=[self.planta.pk]), {
            'edificio': other.pk, 'nombre': 'Baja renombrada', 'orden': -1,
        })
        self.planta.refresh_from_db()
        self.assertEqual(self.planta.edificio_id, self.edificio.pk)
        self.assertEqual(self.planta.nombre, 'Baja renombrada')
        self.client.post(reverse('ubicacion_update', args=[self.espacio.pk]), {
            'planta': self.otra_planta.pk, 'nombre': 'Sala renombrada',
        })
        self.espacio.refresh_from_db()
        self.assertEqual(self.espacio.planta_id, self.planta.pk)
        self.assertEqual(self.espacio.nombre, 'Sala renombrada')
        self.client.post(reverse('edificio_update', args=[self.edificio.pk]), {
            'codigo': 'edi-01', 'nombre': 'Edificio renombrado',
        })
        self.obra.refresh_from_db()
        self.assertIn('Edificio renombrado', self.obra.ubicacion_actual)
        self.assertIn('Sala renombrada', self.obra.ubicacion_actual)

    def test_assign_and_clear_catalog_location_preserves_legacy_and_photos(self):
        FotoObra.objects.create(obra=self.legacy, imagen='obras/fixture-sin-archivo.png')
        datos = {'codigo': self.legacy.codigo, 'titulo': self.legacy.titulo,
                 'tipo': self.legacy.tipo, 'conservacion': self.legacy.conservacion,
                 'ubicacion': self.legacy.ubicacion, 'espacio': self.espacio.pk}
        response = self.client.post(reverse('obra_update', args=[self.legacy.pk]), datos)
        self.assertRedirects(response, self.legacy.get_absolute_url())
        self.legacy.refresh_from_db()
        self.assertEqual(self.legacy.ubicacion, 'Referencia antigua exacta')
        self.assertEqual(self.legacy.espacio_id, self.espacio.pk)
        self.assertEqual(self.legacy.fotos.count(), 1)
        self.assertEqual(self.legacy.ubicacion_actual, str(self.espacio))
        response = self.client.get(self.legacy.get_absolute_url())
        self.assertContains(response, 'Referencia antigua exacta')
        self.client.post(reverse('obra_update', args=[self.legacy.pk]), {**datos, 'espacio': ''})
        self.legacy.refresh_from_db()
        self.assertIsNone(self.legacy.espacio_id)
        self.assertEqual(self.legacy.ubicacion_actual, 'Referencia antigua exacta')

    def test_search_and_building_filter_include_linked_locations(self):
        for query in ('EDI-01', 'Edificio de prueba', 'Planta baja', 'Sala de prueba'):
            response = self.client.get(reverse('obra_list'), {'q': query})
            self.assertContains(response, 'Obra ubicada')
            self.assertNotContains(response, 'Obra anterior')
        response = self.client.get(reverse('obra_list'), {'edificio': self.edificio.pk})
        self.assertContains(response, 'Obra ubicada')
        self.assertNotContains(response, 'Obra anterior')
        self.assertEqual(self.client.get(reverse('obra_list'), {'edificio': 'bad'}).status_code, 200)
        response = self.client.get(self.espacio.get_absolute_url())
        self.assertContains(response, 'Obra ubicada')
        self.assertNotContains(response, 'Obra anterior')

    def test_catalog_search_tree_and_navigation(self):
        for query in ('Edificio de prueba', 'Planta baja', 'Sala de prueba'):
            response = self.client.get(reverse('catalogo'), {'q': query})
            self.assertContains(response, 'Edificio de prueba')
            self.assertContains(response, 'Sala de prueba')
        response = self.client.get(reverse('catalogo'), {'q': 'no-existe'})
        self.assertContains(response, 'No hay edificios que coincidan')
        response = self.client.get(reverse('catalogo'))
        self.assertContains(response, 'aria-current="page"', count=1)
        self.client.force_login(self.lector)
        response = self.client.get(reverse('catalogo'))
        self.assertNotContains(response, 'Añadir edificio')
        self.assertNotContains(response, 'Editar edificio')
        self.assertNotContains(response, 'Añadir planta')

    def test_related_records_cannot_be_deleted(self):
        for obj in (self.edificio, self.planta, self.espacio):
            with self.subTest(obj=obj), self.assertRaises(ProtectedError):
                obj.delete()
        self.assertEqual(Obra.objects.count(), 2)

    def test_location_page_does_not_disclose_works_without_inventory_permission(self):
        self.sin_acceso.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='gebichart', codename__in=[
                'view_edificio', 'view_planta', 'view_ubicacion',
            ],
        ))
        self.client.force_login(self.sin_acceso)
        response = self.client.get(self.espacio.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Obra ubicada')
        self.assertNotContains(self.client.get(reverse('catalogo')), '1 obra')

    def test_write_routes_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        for url in self.urls_escritura():
            self.assertEqual(client.post(url, {}).status_code, 403)

    def test_role_refresh_keeps_memberships_and_does_not_grant_delete(self):
        call_command('crear_roles', stdout=StringIO())
        call_command('crear_roles', stdout=StringIO())
        self.assertTrue(self.lector.groups.filter(name='Consulta inventario').exists())
        for model in ('edificio', 'planta', 'ubicacion'):
            self.assertTrue(self.lector.has_perm(f'gebichart.view_{model}'))
            self.assertFalse(self.lector.has_perm(f'gebichart.change_{model}'))
            self.assertTrue(self.editor.has_perm(f'gebichart.add_{model}'))
            self.assertFalse(self.editor.has_perm(f'gebichart.delete_{model}'))

    def test_catalog_and_location_work_pagination(self):
        Edificio.objects.bulk_create([Edificio(codigo=f'PAGE-{i}', nombre=f'Edificio {i}')
                                     for i in range(11)])
        response = self.client.get(reverse('catalogo'), {'q': 'Edificio', 'page': 2})
        self.assertEqual(response.context['page_obj'].number, 2)
        Obra.objects.bulk_create([Obra(codigo=f'PAGE-{i}', titulo=f'Obra {i}', tipo='pintura',
                                      espacio=self.espacio) for i in range(23)])
        response = self.client.get(self.espacio.get_absolute_url(), {'page': 2})
        self.assertEqual(len(response.context['obras']), 4)

    def test_admin_forms_available_with_permissions(self):
        user = get_user_model().objects.create_superuser('admin-catalogo')
        self.client.force_login(user)
        for model in ('edificio', 'planta', 'ubicacion'):
            self.assertEqual(self.client.get(reverse(f'admin:gebichart_{model}_add')).status_code, 200)
