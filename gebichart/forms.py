from typing import ClassVar

from django import forms

from .models import Obra


class ObraForm(forms.ModelForm):
    # Normalize before validators and the model's uniqueness check run.
    codigo = forms.CharField(
        label='Código de inventario', max_length=50,
        help_text=Obra._meta.get_field('codigo').help_text,
    )

    class Meta:
        model = Obra
        fields = (
            'codigo', 'titulo', 'autoria', 'tipo', 'tecnica', 'datacion',
            'dimensiones', 'conservacion', 'ubicacion', 'descripcion', 'observaciones',
        )
        widgets: ClassVar[dict] = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_codigo(self):
        return self.cleaned_data['codigo'].upper()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'gch-input'
        self.fields['codigo'].widget.attrs['autocapitalize'] = 'characters'


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ValidatedImageField(forms.ImageField):
    def to_python(self, data):
        if data and data.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Cada imagen puede ocupar como máximo 10 MB.')
        image = super().to_python(data)
        if image:
            extensions = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
            extension = extensions.get(image.image.format)
            if not extension:
                raise forms.ValidationError('Solo se admiten imágenes JPG, PNG o WebP.')
            if image.image.width * image.image.height > 40_000_000:
                raise forms.ValidationError('La imagen no puede superar los 40 megapíxeles.')
            # Use the detected format, never a user-provided filename or extension.
            image.name = f'imagen{extension}'
        return image


class MultipleImageField(ValidatedImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        files = list(data) if isinstance(data, (list, tuple)) else ([data] if data else [])
        if not files and self.required:
            raise forms.ValidationError('Selecciona al menos una imagen.')
        if len(files) > 10:
            raise forms.ValidationError('Puedes añadir hasta 10 imágenes por envío.')
        if sum(file.size for file in files) > 50 * 1024 * 1024:
            raise forms.ValidationError('El conjunto de imágenes no puede superar los 50 MB.')
        return [super(MultipleImageField, self).clean(file) for file in files]


class ObraConFotosForm(ObraForm):
    fotos = MultipleImageField(
        label='Añadir fotografías', required=False,
        help_text='Puedes seleccionar varias: JPG, PNG o WebP. Máximo 10 MB por imagen, '
                  '10 imágenes y 50 MB por envío. Las imágenes existentes se conservan.',
        widget=MultipleImageInput(attrs={'class': 'gch-input',
                                        'accept': 'image/jpeg,image/png,image/webp'}),
    )


class GaleriaForm(forms.Form):
    fotos = MultipleImageField(
        label='Seleccionar imágenes',
        help_text='JPG, PNG o WebP. Hasta 10 MB y 40 megapíxeles por imagen. '
                  'Máximo 10 imágenes y 50 MB por envío.',
        widget=MultipleImageInput(attrs={'class': 'gch-input',
                                        'accept': 'image/jpeg,image/png,image/webp'}),
    )
    descripcion = forms.CharField(
        label='Descripción (opcional)', max_length=255, required=False,
        help_text='Se aplica a las imágenes seleccionadas.',
        widget=forms.TextInput(attrs={'class': 'gch-input'}),
    )
