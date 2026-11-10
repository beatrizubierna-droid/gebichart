from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from gebichart import views

admin.site.site_header = 'Administración de GEBICHART'
admin.site.site_title = 'GEBICHART'
admin.site.index_title = 'Gestión de obras, usuarios y permisos'

urlpatterns = [
    path('', views.home, name='home'),
    path('acceso/', auth_views.LoginView.as_view(), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('inventario/', views.ObraListView.as_view(), name='obra_list'),
    path('inventario/nueva/', views.ObraCreateView.as_view(), name='obra_create'),
    path('inventario/<int:pk>/', views.ObraDetailView.as_view(), name='obra_detail'),
    path('inventario/<int:pk>/editar/', views.ObraUpdateView.as_view(), name='obra_update'),
    path('admin/', admin.site.urls),
]
