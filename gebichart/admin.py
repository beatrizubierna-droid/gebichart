from django.contrib import admin
from django.utils.html import format_html

from .forms import ObraForm
from .models import Obra


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    form = ObraForm
    list_display = ('codigo', 'titulo', 'autoria', 'tipo', 'ubicacion', 'conservacion')
    list_filter = ('tipo', 'conservacion')
    search_fields = ('codigo', 'titulo', 'autoria', 'ubicacion')
    readonly_fields = ('creado_en', 'actualizado_en', 'galeria')

    @admin.display(description='Galería de imágenes')
    def galeria(self, obj):
        if not obj or not obj.pk:
            return 'Guarda la obra y abre su ficha para añadir fotografías.'
        return format_html('<a href="{}#galeria">Ver y gestionar fotografías ({})</a>',
                           obj.get_absolute_url(), obj.fotos.count())
