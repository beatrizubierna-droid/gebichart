from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import GaleriaForm, ObraConFotosForm
from .gallery import gallery_transaction, guardar_fotos
from .models import FotoObra, Obra


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['galeria_form'] = GaleriaForm()
        return context


class ObraSaveMixin(InventarioAccessMixin):
    model = Obra
    form_class = ObraConFotosForm
    template_name = 'gebichart/obra_form.html'

    def form_valid(self, form):
        with gallery_transaction() as nuevas:
            response = super().form_valid(form)
            guardar_fotos(self.object, form.cleaned_data['fotos'], nuevas)
        messages.success(self.request, f'Obra {self.object.codigo} guardada correctamente.')
        return response


class ObraCreateView(ObraSaveMixin, CreateView):
    permission_required = ('gebichart.view_obra', 'gebichart.add_obra')


class ObraUpdateView(ObraSaveMixin, UpdateView):
    permission_required = ('gebichart.view_obra', 'gebichart.change_obra')


class FotoUploadView(InventarioAccessMixin, View):
    permission_required = ('gebichart.view_obra', 'gebichart.change_obra')

    def post(self, request, obra_pk):
        obra = get_object_or_404(Obra, pk=obra_pk)
        form = GaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            with gallery_transaction() as nuevas:
                guardar_fotos(obra, form.cleaned_data['fotos'], nuevas,
                              form.cleaned_data['descripcion'])
            messages.success(request, f'{len(nuevas)} imagen(es) añadida(s) a la galería.')
            return redirect(f'{obra.get_absolute_url()}#galeria')
        return render(request, 'gebichart/obra_detail.html', {
            'obra': obra, 'galeria_form': form,
        })


class FotoFileView(InventarioAccessMixin, View):
    def get(self, request, obra_pk, pk):
        foto = get_object_or_404(FotoObra, obra_id=obra_pk, pk=pk)
        try:
            archivo = foto.imagen.open('rb')
        except FileNotFoundError as exc:
            raise Http404('Imagen no disponible.') from exc
        response = FileResponse(archivo, content_type={
            '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
        }.get('.' + foto.imagen.name.rsplit('.', 1)[-1], 'application/octet-stream'))
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class FotoDeleteView(InventarioAccessMixin, DeleteView):
    permission_required = ('gebichart.view_obra', 'gebichart.change_obra')
    model = FotoObra
    context_object_name = 'foto'
    template_name = 'gebichart/foto_confirm_delete.html'

    def get_queryset(self):
        return super().get_queryset().filter(obra_id=self.kwargs['obra_pk']).select_related('obra')

    def get_success_url(self):
        return reverse('obra_detail', kwargs={'pk': self.object.obra_id}) + '#galeria'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Imagen eliminada de la galería.')
        return response
