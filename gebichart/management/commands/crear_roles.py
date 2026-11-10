from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Crea grupos de consulta y gestión del inventario, sin asignar usuarios.'

    def handle(self, *args, **options):
        modelos = ('obra', 'edificio', 'planta', 'ubicacion')
        roles = {
            'Consulta inventario': [f'view_{model}' for model in modelos],
            'Gestión inventario': [f'{action}_{model}' for model in modelos
                                  for action in ('view', 'add', 'change')],
        }
        for nombre, codigos in roles.items():
            permissions = Permission.objects.filter(
                content_type__app_label='gebichart', content_type__model__in=modelos,
                codename__in=codigos,
            )
            if permissions.count() != len(codigos):
                raise CommandError('Ejecuta primero python manage.py migrate.')
            group, _ = Group.objects.get_or_create(name=nombre)
            group.permissions.add(*permissions)
            self.stdout.write(self.style.SUCCESS(f'Grupo preparado: {nombre}'))
