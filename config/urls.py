from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from gebichart import catalogo, reports, views

admin.site.site_header = 'Administración de GEBICHART'
admin.site.site_title = 'GEBICHART'
admin.site.index_title = 'Gestión de obras, usuarios y permisos'

urlpatterns = [
    path('', views.home, name='home'),
    path('acceso/', auth_views.LoginView.as_view(), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('inventario/', views.ObraListView.as_view(), name='obra_list'),
    path('inventario/imprimir/', reports.ObrasPrintView.as_view(), name='obras_print'),
    path('inventario/nueva/', views.ObraCreateView.as_view(), name='obra_create'),
    path('inventario/<int:pk>/', views.ObraDetailView.as_view(), name='obra_detail'),
    path('inventario/<int:pk>/editar/', views.ObraUpdateView.as_view(), name='obra_update'),
    path('inventario/<int:obra_pk>/imagenes/subir/', views.FotoUploadView.as_view(),
         name='foto_upload'),
    path('inventario/<int:obra_pk>/imagenes/<int:pk>/archivo/', views.FotoFileView.as_view(),
         name='foto_file'),
    path('inventario/<int:obra_pk>/imagenes/<int:pk>/eliminar/', views.FotoDeleteView.as_view(),
         name='foto_delete'),
    path('ubicaciones/', catalogo.CatalogoListView.as_view(), name='catalogo'),
    path('ubicaciones/imprimir/', reports.CatalogoPrintView.as_view(), name='catalogo_print'),
    path('ubicaciones/espacios/<int:pk>/imprimir/', reports.UbicacionObrasPrintView.as_view(),
         name='ubicacion_obras_print'),
    path('ubicaciones/edificios/nuevo/', catalogo.EdificioCreateView.as_view(), name='edificio_create'),
    path('ubicaciones/edificios/<int:pk>/editar/', catalogo.EdificioUpdateView.as_view(),
         name='edificio_update'),
    path('ubicaciones/plantas/nueva/', catalogo.PlantaCreateView.as_view(), name='planta_create'),
    path('ubicaciones/plantas/<int:pk>/editar/', catalogo.PlantaUpdateView.as_view(), name='planta_update'),
    path('ubicaciones/espacios/nuevo/', catalogo.UbicacionCreateView.as_view(), name='ubicacion_create'),
    path('ubicaciones/espacios/<int:pk>/', catalogo.UbicacionDetailView.as_view(), name='ubicacion_detail'),
    path('ubicaciones/espacios/<int:pk>/editar/', catalogo.UbicacionUpdateView.as_view(),
         name='ubicacion_update'),
    path('usuarios/', reports.UsuariosListView.as_view(), name='usuarios_list'),
    path('usuarios/imprimir/', reports.UsuariosPrintView.as_view(), name='usuarios_print'),
    path('admin/', admin.site.urls),
]
