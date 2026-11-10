from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import GaleriaForm, ValidatedImageField
from .models import FotoObra, Obra


def image_file(name='foto.png', fmt='PNG'):
    output = BytesIO()
    Image.new('RGB', (24, 16), color='#993333').save(output, format=fmt)
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/png')


class GaleriaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.editor = users.objects.create_user('editor-fotos')
        cls.lector = users.objects.create_user('lector-fotos')
        cls.sin_acceso = users.objects.create_user('sin-fotos', is_staff=True)
        call_command('crear_roles', stdout=StringIO())
        cls.editor.groups.add(Group.objects.get(name='Gestión inventario'))
        cls.lector.groups.add(Group.objects.get(name='Consulta inventario'))
        cls.obra = Obra.objects.create(codigo='FOTO-001', titulo='Obra con fotos', tipo='pintura')
        cls.otra = Obra.objects.create(codigo='FOTO-002', titulo='Otra obra', tipo='escultura')

    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=self.media.name))
        self.client.force_login(self.editor)

    def upload_url(self, obra=None):
        return reverse('foto_upload', args=[(obra or self.obra).pk])

    def add_photo(self, obra=None):
        self.client.post(self.upload_url(obra), {'fotos': [image_file()]})
        return (obra or self.obra).fotos.latest('pk')

    def delete_url(self, foto, obra=None):
        return reverse('foto_delete', args=[(obra or self.obra).pk, foto.pk])

    def files_on_disk(self):
        return [p for p in Path(self.media.name).rglob('*') if p.is_file()]

    def test_upload_multiple_images_and_keep_original_bytes(self):
        first, second = image_file(), image_file(fmt='JPEG')
        original = first.read()
        first.seek(0)
        response = self.client.post(self.upload_url(), {
            'fotos': [first, second], 'descripcion': 'Vista de conjunto',
        })
        self.assertRedirects(response, self.obra.get_absolute_url() + '#galeria')
        self.assertEqual(self.obra.fotos.count(), 2)
        self.assertTrue(all(f.descripcion == 'Vista de conjunto' for f in self.obra.fotos.all()))
        foto = self.obra.fotos.first()
        self.assertEqual(foto.imagen.read(), original)
        foto.imagen.close()
        self.assertNotIn('foto.png', foto.imagen.name)
        self.assertEqual(len(self.files_on_disk()), 2)

    def test_supported_formats_are_detected_and_canonicalized(self):
        for fmt, suffix in [('JPEG', '.jpg'), ('PNG', '.png'), ('WEBP', '.webp')]:
            with self.subTest(fmt=fmt):
                self.client.post(self.upload_url(), {'fotos': [image_file('upload.html', fmt)]})
                foto = self.obra.fotos.latest('pk')
                self.assertTrue(foto.imagen.name.endswith(suffix))

    def test_invalid_file_rejects_entire_batch(self):
        response = self.client.post(self.upload_url(), {'fotos': [
            image_file(), SimpleUploadedFile('falso.jpg', b'<script>bad</script>'),
        ]})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se ha añadido ninguna imagen.')
        self.assertEqual(self.obra.fotos.count(), 0)
        self.assertEqual(self.files_on_disk(), [])

    def test_empty_upload_and_unsupported_formats_rejected(self):
        response = self.client.post(self.upload_url(), {})
        self.assertContains(response, 'Selecciona al menos una imagen.')
        response = self.client.post(self.upload_url(), {'fotos': [image_file('animacion.gif', 'GIF')]})
        self.assertContains(response, 'Solo se admiten imágenes JPG, PNG o WebP.')
        self.assertEqual(FotoObra.objects.count(), 0)

    def test_count_size_and_pixel_limits(self):
        form = GaleriaForm({}, {'fotos': [image_file() for _ in range(11)]})
        self.assertFalse(form.is_valid())
        self.assertIn('10 imágenes', str(form.errors))
        large = image_file()
        large.size = 10 * 1024 * 1024 + 1
        form = GaleriaForm({}, {'fotos': [large]})
        self.assertFalse(form.is_valid())
        self.assertIn('10 MB', str(form.errors))
        files = [image_file() for _ in range(6)]
        for file in files:
            file.size = 9 * 1024 * 1024
        form = GaleriaForm({}, {'fotos': files})
        self.assertFalse(form.is_valid())
        self.assertIn('50 MB', str(form.errors))
        with patch('django.forms.ImageField.to_python') as parent:
            parent.return_value.image.format = 'PNG'
            parent.return_value.image.width = 8000
            parent.return_value.image.height = 6000
            with self.assertRaisesMessage(ValidationError, '40 megapíxeles'):
                ValidatedImageField().clean(image_file())

    def test_add_photos_during_artwork_creation_and_editing(self):
        response = self.client.post(reverse('obra_create'), {
            'codigo': 'FOTO-003', 'titulo': 'Nueva obra', 'tipo': 'pintura',
            'conservacion': 'sin_evaluar', 'fotos': [image_file(), image_file()],
        })
        obra = Obra.objects.get(codigo='FOTO-003')
        self.assertRedirects(response, obra.get_absolute_url())
        self.assertEqual(obra.fotos.count(), 2)
        datos = {'codigo': obra.codigo, 'titulo': obra.titulo, 'tipo': obra.tipo,
                 'conservacion': obra.conservacion}
        self.client.post(reverse('obra_update', args=[obra.pk]), datos)
        self.assertEqual(obra.fotos.count(), 2)
        self.client.post(reverse('obra_update', args=[obra.pk]), {**datos, 'fotos': [image_file()]})
        self.assertEqual(obra.fotos.count(), 3)

    def test_invalid_photos_do_not_create_or_modify_artwork(self):
        datos = {'codigo': 'FOTO-003', 'titulo': 'Nueva obra', 'tipo': 'pintura',
                 'conservacion': 'sin_evaluar',
                 'fotos': [SimpleUploadedFile('falso.png', b'invalid')]}
        response = self.client.post(reverse('obra_create'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Obra.objects.filter(codigo='FOTO-003').exists())
        datos['codigo'] = self.obra.codigo
        datos['fotos'] = [SimpleUploadedFile('falso.png', b'invalid')]
        self.client.post(reverse('obra_update', args=[self.obra.pk]), datos)
        self.obra.refresh_from_db()
        self.assertEqual(self.obra.titulo, 'Obra con fotos')
        self.assertEqual(self.files_on_disk(), [])

    def test_reader_can_see_images_but_cannot_upload_or_delete(self):
        foto = self.add_photo()
        self.client.force_login(self.lector)
        response = self.client.get(foto.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        response.close()
        response = self.client.get(self.obra.get_absolute_url())
        self.assertContains(response, 'Galería de imágenes')
        self.assertNotContains(response, 'Subir imágenes')
        self.assertNotContains(response, 'Eliminar imagen')
        self.assertEqual(self.client.post(self.upload_url(), {'fotos': [image_file()]}).status_code,
                         403)
        self.assertEqual(self.client.get(self.delete_url(foto)).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url(foto)).status_code, 403)
        self.assertTrue(FotoObra.objects.filter(pk=foto.pk).exists())

    def test_photos_are_not_public_even_for_staff_without_permissions(self):
        foto = self.add_photo()
        self.client.logout()
        self.assertEqual(self.client.get(foto.get_absolute_url()).status_code, 302)
        self.assertEqual(self.client.post(self.upload_url(), {'fotos': [image_file()]}).status_code,
                         302)
        self.client.force_login(self.sin_acceso)
        self.assertEqual(self.client.get(foto.get_absolute_url()).status_code, 403)
        self.assertEqual(self.client.post(self.upload_url(), {'fotos': [image_file()]}).status_code,
                         403)
        self.assertEqual(self.client.post(self.delete_url(foto)).status_code, 403)
        self.assertEqual(self.client.get(foto.imagen.url).status_code, 404)

    def test_photo_must_belong_to_url_artwork(self):
        foto = self.add_photo()
        self.assertEqual(self.client.get(reverse('foto_file', args=[self.otra.pk, foto.pk])).status_code,
                         404)
        self.assertEqual(self.client.post(self.delete_url(foto, self.otra)).status_code, 404)
        self.assertTrue(FotoObra.objects.filter(pk=foto.pk).exists())

    def test_delete_requires_confirmation_and_removes_file_after_commit(self):
        foto = self.add_photo()
        path = Path(foto.imagen.path)
        response = self.client.get(self.delete_url(foto))
        self.assertContains(response, 'Confirmar eliminación')
        self.assertTrue(path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.delete_url(foto))
        self.assertRedirects(response, self.obra.get_absolute_url() + '#galeria')
        self.assertFalse(path.exists())
        self.assertFalse(FotoObra.objects.filter(pk=foto.pk).exists())

    def test_cascade_deletion_cleans_files(self):
        foto = self.add_photo()
        path = Path(foto.imagen.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.obra.delete()
        self.assertFalse(path.exists())

    def test_rollback_does_not_delete_image_file(self):
        foto = self.add_photo()
        path = Path(foto.imagen.path)
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    FotoObra.objects.get(pk=foto.pk).delete()
                    raise ValueError('rollback')
            except ValueError:
                pass
        self.assertTrue(FotoObra.objects.filter(pk=foto.pk).exists())
        self.assertTrue(path.exists())

    def test_storage_failure_rolls_back_rows_and_cleans_partial_upload(self):
        original_save = FotoObra.save
        calls = []

        def failing_save(instance, *args, **kwargs):
            calls.append(instance)
            if len(calls) == 2:
                raise OSError('storage unavailable')
            return original_save(instance, *args, **kwargs)

        with patch.object(FotoObra, 'save', failing_save), self.assertRaises(OSError):
            self.client.post(reverse('obra_create'), {
                'codigo': 'FOTO-003', 'titulo': 'No debe guardarse', 'tipo': 'pintura',
                'conservacion': 'sin_evaluar', 'fotos': [image_file(), image_file()],
            })
        self.assertFalse(Obra.objects.filter(codigo='FOTO-003').exists())
        self.assertEqual(FotoObra.objects.count(), 0)
        self.assertEqual(self.files_on_disk(), [])

    def test_upload_and_deletion_require_csrf(self):
        foto = self.add_photo()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        self.assertEqual(client.post(self.upload_url(), {'fotos': [image_file()]}).status_code, 403)
        self.assertEqual(client.post(self.delete_url(foto)).status_code, 403)
        self.assertTrue(FotoObra.objects.filter(pk=foto.pk).exists())

    def test_gallery_caption_is_escaped(self):
        self.client.post(self.upload_url(), {
            'fotos': [image_file()], 'descripcion': '<script>alert(1)</script>',
        })
        response = self.client.get(self.obra.get_absolute_url())
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_missing_stored_file_returns_404(self):
        foto = self.add_photo()
        Path(foto.imagen.path).unlink()
        self.assertEqual(self.client.get(foto.get_absolute_url()).status_code, 404)
