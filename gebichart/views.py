from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ObraForm
from .models import Obra


@login_required
def home(request):
    total = Obra.objects.count() if request.user.has_perm('gebichart.view_obra') else None
    return render(request, 'gebichart/home.html', {'total_obras': total})


class InventarioAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'gebichart.view_obra'


class ObraListView(InventarioAccessMixin, ListView):
    model = Obra
    template_name = 'gebichart/obra_list.html'
    context_object_name = 'obras'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) | Q(titulo__icontains=query)
                | Q(autoria__icontains=query) | Q(ubicacion__icontains=query)
            )
        tipo = self.request.GET.get('tipo', '')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        conservacion = self.request.GET.get('conservacion', '')
        if conservacion:
            queryset = queryset.filter(conservacion=conservacion)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        context.update({
            'q': self.request.GET.get('q', '').strip(),
            'tipo': self.request.GET.get('tipo', ''),
            'conservacion': self.request.GET.get('conservacion', ''),
            'tipos': Obra.Tipo.choices,
            'estados': Obra.Conservacion.choices,
            'filtros': params.urlencode(),
        })
        return context


class ObraDetailView(InventarioAccessMixin, DetailView):
    model = Obra
    template_name = 'gebichart/obra_detail.html'
    context_object_name = 'obra'


class ObraSaveMixin(InventarioAccessMixin):
    model = Obra
    form_class = ObraForm
    template_name = 'gebichart/obra_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Obra {self.object.codigo} guardada correctamente.')
        return response


class ObraCreateView(ObraSaveMixin, CreateView):
    permission_required = ('gebichart.view_obra', 'gebichart.add_obra')


class ObraUpdateView(ObraSaveMixin, UpdateView):
    permission_required = ('gebichart.view_obra', 'gebichart.change_obra')
