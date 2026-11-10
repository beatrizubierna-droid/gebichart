from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


class Obra(models.Model):
    class Tipo(models.TextChoices):
        PINTURA = 'pintura', 'Pintura'
        ESCULTURA = 'escultura', 'Escultura'
        DIBUJO = 'dibujo', 'Dibujo'
        GRABADO = 'grabado', 'Grabado'
        FOTOGRAFIA = 'fotografia', 'Fotografía'
        DECORATIVAS = 'artes_decorativas', 'Artes decorativas'
        OTRO = 'otro', 'Otro'

    class Conservacion(models.TextChoices):
        SIN_EVALUAR = 'sin_evaluar', 'Sin evaluar'
        BUENO = 'bueno', 'Bueno'
        REGULAR = 'regular', 'Regular'
        MALO = 'malo', 'Malo'

    codigo = models.CharField(
        'código de inventario', max_length=50, unique=True,
        validators=[RegexValidator(
            r'^[A-Z0-9][A-Z0-9._/-]*$',
            'Usa letras A–Z, números, puntos, guiones, barras o guiones bajos.',
        )],
        help_text='Identificador único. Se guarda en mayúsculas, sin espacios.',
    )
    titulo = models.CharField('título', max_length=255)
    autoria = models.CharField('autoría', max_length=200, blank=True)
    tipo = models.CharField('tipo de bien', max_length=20, choices=Tipo.choices)
    tecnica = models.CharField('técnica y materiales', max_length=255, blank=True)
    datacion = models.CharField('datación', max_length=100, blank=True,
                               help_text='Por ejemplo: siglo XIX, ca. 1920 o fecha desconocida.')
    dimensiones = models.CharField('dimensiones', max_length=200, blank=True,
                                  help_text='Incluye las unidades y el orden de las medidas.')
    conservacion = models.CharField('estado de conservación', max_length=20,
                                   choices=Conservacion.choices,
                                   default=Conservacion.SIN_EVALUAR)
    ubicacion = models.CharField('ubicación actual', max_length=255, blank=True,
                                help_text='Edificio, planta y sala, si se conocen.')
    descripcion = models.TextField('descripción', blank=True, max_length=10000)
    observaciones = models.TextField('observaciones', blank=True, max_length=10000)
    creado_en = models.DateTimeField('fecha de alta', auto_now_add=True)
    actualizado_en = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ('codigo', 'pk')
        verbose_name = 'obra'
        verbose_name_plural = 'obras'

    def __str__(self):
        return f'{self.codigo} · {self.titulo}'

    def get_absolute_url(self):
        return reverse('obra_detail', kwargs={'pk': self.pk})


def foto_upload_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4

    return f'obras/{instance.obra_id}/{uuid4().hex}{Path(filename).suffix.lower()}'


class FotoObra(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField('imagen', upload_to=foto_upload_path, max_length=200)
    descripcion = models.CharField('descripción', max_length=255, blank=True)
    creado_en = models.DateTimeField('fecha de subida', auto_now_add=True)

    class Meta:
        ordering = ('creado_en', 'pk')
        verbose_name = 'fotografía de obra'
        verbose_name_plural = 'fotografías de obras'

    def get_absolute_url(self):
        return reverse('foto_file', kwargs={'obra_pk': self.obra_id, 'pk': self.pk})

    def __str__(self):
        return f'Fotografía de {self.obra.codigo}'
