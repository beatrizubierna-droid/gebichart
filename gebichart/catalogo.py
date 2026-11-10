from typing import ClassVar

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import EdificioForm, PlantaForm, UbicacionForm
from .models import Edificio, Obra, Planta, Ubicacion

CATALOGO_READ = ('gebichart.view_edificio', 'gebichart.view_planta', 'gebichart.view_ubicacion')


class CatalogoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = CATALOGO_READ


class CatalogoListView(CatalogoAccessMixin, ListView):
    model = Edificio
    context_object_name = 'edificios'
    template_name = 'gebichart/catalogo_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        selected = self.request.GET.get('edificio', '')
        if selected:
            queryset = queryset.filter(pk=selected) if selected.isdecimal() else queryset.none()
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(direccion__icontains=q)
                | Q(plantas__nombre__icontains=q) | Q(plantas__ubicaciones__nombre__icontains=q)
            ).distinct()
        return queryset.prefetch_related(Prefetch(
            'plantas', queryset=Planta.objects.prefetch_related(Prefetch(
                'ubicaciones', queryset=Ubicacion.objects.annotate(total_obras=Count('obras')),
            )),
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edificio_seleccionado'] = self.request.GET.get('edificio', '')
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class CatalogoSaveMixin(CatalogoAccessMixin):
    template_name = 'gebichart/catalogo_form.html'

    def get_initial(self):
        initial = super().get_initial()
        # Only preselect existing parents; form choices validate every submitted ID.
        for field, model in (('edificio', Edificio), ('planta', Planta)):
            value = self.request.GET.get(field, '')
            if (field in self.form_class.base_fields and value.isdecimal()
                    and model.objects.filter(pk=value).exists()):
                initial[field] = value
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Datos del catálogo guardados correctamente.')
        return response


class EdificioCreateView(CatalogoSaveMixin, CreateView):
    model = Edificio
    form_class = EdificioForm
    permission_required = (*CATALOGO_READ, 'gebichart.add_edificio')
    extra_context: ClassVar[dict] = {'titulo': 'Añadir edificio'}


class EdificioUpdateView(CatalogoSaveMixin, UpdateView):
    model = Edificio
    form_class = EdificioForm
    permission_required = (*CATALOGO_READ, 'gebichart.change_edificio')
    extra_context: ClassVar[dict] = {'titulo': 'Editar edificio'}


class PlantaCreateView(CatalogoSaveMixin, CreateView):
    model = Planta
    form_class = PlantaForm
    permission_required = (*CATALOGO_READ, 'gebichart.add_planta')
    extra_context: ClassVar[dict] = {'titulo': 'Añadir planta'}


class PlantaUpdateView(CatalogoSaveMixin, UpdateView):
    model = Planta
    form_class = PlantaForm
    permission_required = (*CATALOGO_READ, 'gebichart.change_planta')
    extra_context: ClassVar[dict] = {'titulo': 'Editar planta'}


class UbicacionCreateView(CatalogoSaveMixin, CreateView):
    model = Ubicacion
    form_class = UbicacionForm
    permission_required = (*CATALOGO_READ, 'gebichart.add_ubicacion')
    extra_context: ClassVar[dict] = {'titulo': 'Añadir ubicación'}


class UbicacionUpdateView(CatalogoSaveMixin, UpdateView):
    model = Ubicacion
    form_class = UbicacionForm
    permission_required = (*CATALOGO_READ, 'gebichart.change_ubicacion')
    extra_context: ClassVar[dict] = {'titulo': 'Editar ubicación'}


class UbicacionDetailView(CatalogoAccessMixin, DetailView):
    model = Ubicacion
    queryset = Ubicacion.objects.select_related('planta__edificio')
    context_object_name = 'ubicacion'
    template_name = 'gebichart/ubicacion_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['obras'] = None
        if self.request.user.has_perm('gebichart.view_obra'):
            context['obras'] = Paginator(Obra.objects.filter(espacio=self.object), 20).get_page(
                self.request.GET.get('page')
            )
        return context
