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
