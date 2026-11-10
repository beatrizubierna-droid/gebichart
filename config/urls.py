from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from gebichart.views import home

admin.site.site_header = 'Administración de GEBICHART'
admin.site.site_title = 'GEBICHART'
admin.site.index_title = 'Gestión de usuarios y permisos'

urlpatterns = [
    path('', home, name='home'),
    path('acceso/', auth_views.LoginView.as_view(), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
]
