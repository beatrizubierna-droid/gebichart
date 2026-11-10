from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import FotoObra


@receiver(post_delete, sender=FotoObra)
def delete_photo_file(sender, instance, **kwargs):
    # A rollback must keep the file; includes cascade deletion of an artwork.
    if instance.imagen:
        storage, name = instance.imagen.storage, instance.imagen.name
        transaction.on_commit(lambda: storage.delete(name))
