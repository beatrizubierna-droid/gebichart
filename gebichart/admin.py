from django.contrib import admin

from .forms import ObraForm
from .models import Obra


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    form = ObraForm
    list_display = ('codigo', 'titulo', 'autoria', 'tipo', 'ubicacion', 'conservacion')
    list_filter = ('tipo', 'conservacion')
    search_fields = ('codigo', 'titulo', 'autoria', 'ubicacion')
    readonly_fields = ('creado_en', 'actualizado_en')
