from typing import ClassVar

from django import forms

from .models import Edificio, Obra, Planta, Ubicacion


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
            'dimensiones', 'conservacion', 'espacio', 'ubicacion', 'descripcion', 'observaciones',
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
        self.fields['espacio'].queryset = Ubicacion.objects.select_related('planta__edificio')
        self.fields['espacio'].empty_label = 'Sin asignar al catálogo'
        self.fields['ubicacion'].label = 'Ubicación en texto libre'
        self.fields['ubicacion'].help_text = (
            'Se conserva como referencia. Si seleccionas un espacio del catálogo, '
            'ese espacio será la ubicación actual.'
        )


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


class CatalogoFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'gch-input'
        if self.instance.pk:
            # Keep the hierarchy stable when its labels are edited.
            for parent in ('edificio', 'planta'):
                if parent in self.fields:
                    self.fields[parent].disabled = True
                    self.fields[parent].help_text = 'La pertenencia de un espacio existente se conserva.'


class EdificioForm(CatalogoFormMixin, forms.ModelForm):
    class Meta:
        model = Edificio
        fields = ('codigo', 'nombre', 'direccion', 'descripcion')
        widgets: ClassVar[dict] = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def clean_codigo(self):
        return self.cleaned_data['codigo'].upper()


class PlantaForm(CatalogoFormMixin, forms.ModelForm):
    class Meta:
        model = Planta
        fields = ('edificio', 'nombre', 'orden')


class UbicacionForm(CatalogoFormMixin, forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ('planta', 'nombre', 'descripcion')
        widgets: ClassVar[dict] = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['planta'].queryset = Planta.objects.select_related('edificio')
