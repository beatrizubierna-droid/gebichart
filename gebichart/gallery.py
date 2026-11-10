from contextlib import contextmanager

from django.db import transaction

from .models import FotoObra


@contextmanager
def gallery_transaction():
    """Roll back database rows and clean files if a batch cannot be saved."""
    nuevas = []
    try:
        with transaction.atomic():
            yield nuevas
    except Exception:
        for foto in nuevas:
            if foto.imagen and foto.imagen._committed:
                foto.imagen.delete(save=False)
        raise


def guardar_fotos(obra, uploads, nuevas, descripcion=''):
    for upload in uploads:
        foto = FotoObra(obra=obra, imagen=upload, descripcion=descripcion)
        nuevas.append(foto)
        foto.save()
