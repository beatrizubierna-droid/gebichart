from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView

from .catalogo import CATALOGO_READ, CatalogoListView
from .models import Edificio, Obra, Ubicacion
from .views import ObraListView

USER_READ = f'{get_user_model()._meta.app_label}.view_{get_user_model()._meta.model_name}'


def filtered_query(request, fields):
    return urlencode({key: request.GET[key] for key in fields if request.GET.get(key)})


class PrivateListMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response


class UsuariosListView(PrivateListMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = get_user_model()
    permission_required = USER_READ
    template_name = 'gebichart/usuarios_list.html'
    context_object_name = 'usuarios'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().order_by('username', 'pk').prefetch_related('groups')
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) | Q(first_name__icontains=q)
                | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(groups__name__icontains=q)
            ).distinct()
        activo = self.request.GET.get('activo', '')
        if activo:
            queryset = (queryset.filter(is_active=activo == '1')
                        if activo in ('0', '1') else queryset.none())
        grupo = self.request.GET.get('grupo', '')
        if grupo:
            queryset = queryset.filter(groups__pk=grupo) if grupo.isdecimal() else queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'q': self.request.GET.get('q', '').strip(),
            'activo': self.request.GET.get('activo', ''),
            'grupo': self.request.GET.get('grupo', ''),
            'grupos': Group.objects.order_by('name'),
            'filtros': filtered_query(self.request, ('q', 'activo', 'grupo')),
        })
        return context


class PrintContextMixin(PrivateListMixin):
    paginate_by = None
    report_title = 'Listado'
    return_url_name = 'home'
    filter_fields = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = filtered_query(self.request, (key for key, _ in self.filter_fields))
        context.update({
            'report_title': self.report_title,
            'report_date': timezone.localtime(),
            'report_total': len(self.object_list),
            'report_filters': [(label, self.filter_display(key, self.request.GET[key]))
                               for key, label in self.filter_fields if self.request.GET.get(key)],
            'return_url': reverse(self.return_url_name) + ('?' + query if query else ''),
        })
        return context

    def filter_display(self, key, value):
        if key in ('edificio', 'grupo'):
            model = Edificio if key == 'edificio' else Group
            obj = model.objects.filter(pk=value).first() if value.isdecimal() else None
            return str(obj) if obj else 'Sin coincidencias'
        choices = {'tipo': dict(Obra.Tipo.choices),
                   'conservacion': dict(Obra.Conservacion.choices),
                   'activo': {'1': 'Activos', '0': 'Inactivos'}}
        return choices.get(key, {}).get(value, value)


class ObrasPrintView(PrintContextMixin, ObraListView):
    template_name = 'gebichart/print_obras.html'
    report_title = 'Listado de obras'
    return_url_name = 'obra_list'
    filter_fields = (('q', 'Búsqueda'), ('tipo', 'Tipo'), ('conservacion', 'Conservación'),
                     ('edificio', 'Edificio'))


class CatalogoPrintView(PrintContextMixin, CatalogoListView):
    template_name = 'gebichart/print_catalogo.html'
    report_title = 'Edificios, plantas y ubicaciones'
    return_url_name = 'catalogo'
    filter_fields = (('q', 'Búsqueda'), ('edificio', 'Edificio'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plantas = [planta for edificio in self.object_list for planta in edificio.plantas.all()]
        context['report_plantas'] = len(plantas)
        context['report_ubicaciones'] = sum(len(planta.ubicaciones.all()) for planta in plantas)
        return context


class UsuariosPrintView(PrintContextMixin, UsuariosListView):
    template_name = 'gebichart/print_usuarios.html'
    report_title = 'Listado de usuarios'
    return_url_name = 'usuarios_list'
    filter_fields = (('q', 'Búsqueda'), ('activo', 'Estado'), ('grupo', 'Grupo'))


class UbicacionObrasPrintView(ObrasPrintView):
    permission_required = (*CATALOGO_READ, 'gebichart.view_obra')
    filter_fields = ()

    def get_queryset(self):
        self.ubicacion = get_object_or_404(Ubicacion.objects.select_related('planta__edificio'),
                                         pk=self.kwargs['pk'])
        return Obra.objects.select_related('espacio__planta__edificio').filter(espacio=self.ubicacion)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = f'Obras en {self.ubicacion.nombre}'
        context['report_filters'] = [('Ubicación', str(self.ubicacion))]
        context['return_url'] = self.ubicacion.get_absolute_url()
        return context
