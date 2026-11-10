from django.contrib import admin
from django.utils.html import format_html

from .forms import EdificioForm, ObraForm, PlantaForm, UbicacionForm
from .models import Edificio, Obra, Planta, Ubicacion


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    form = ObraForm
    list_display = ('codigo', 'titulo', 'autoria', 'tipo', 'ubicacion_actual', 'conservacion')
    list_filter = ('tipo', 'conservacion', 'espacio__planta__edificio')
    list_select_related = ('espacio__planta__edificio',)
    search_fields = ('codigo', 'titulo', 'autoria', 'ubicacion', 'espacio__nombre',
                     'espacio__planta__nombre', 'espacio__planta__edificio__nombre',
                     'espacio__planta__edificio__codigo')
    readonly_fields = ('creado_en', 'actualizado_en', 'galeria')

    @admin.display(description='Galería de imágenes')
    def galeria(self, obj):
        if not obj or not obj.pk:
            return 'Guarda la obra y abre su ficha para añadir fotografías.'
        return format_html('<a href="{}#galeria">Ver y gestionar fotografías ({})</a>',
                           obj.get_absolute_url(), obj.fotos.count())


@admin.register(Edificio)
class EdificioAdmin(admin.ModelAdmin):
    form = EdificioForm
    list_display = ('codigo', 'nombre', 'direccion')
    search_fields = ('codigo', 'nombre', 'direccion')


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    form = PlantaForm
    list_display = ('nombre', 'edificio', 'orden')
    list_filter = ('edificio',)
    list_select_related = ('edificio',)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    form = UbicacionForm
    list_display = ('nombre', 'planta')
    list_filter = ('planta__edificio',)
    list_select_related = ('planta__edificio',)
