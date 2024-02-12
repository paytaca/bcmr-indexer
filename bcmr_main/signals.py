from django.db.models.signals import post_save
from django.dispatch import receiver
from bcmr_main.tasks import resolve_metadata
from bcmr_main.op_return import process_op_return
from bcmr_main.models import Registry, Token, TokenMetadata


@receiver(post_save, sender=Registry)
def validate_registry(sender, instance=None, created=False, **kwargs):
    if instance.validity_checks:
        validity_checks = instance.validity_checks
        is_valid = list(validity_checks.values()).count(True) == len(validity_checks.keys())
        Registry.objects.filter(id=instance.id).update(valid=is_valid)


@receiver(post_save, sender=Token)
def generate_metadata(sender, instance=None, created=False, **kwargs):
    try:
        metadata = TokenMetadata.objects.filter(token__category=instance.category).latest('id')
        registry = metadata.registry
        if registry.watch_for_changes:
            process_op_return(
                registry.txid,
                registry.index,
                registry.op_return,
                registry.publisher,
                registry.date_created
            )
        resolve_metadata.delay(registry.id, instance.commitment)
    except TokenMetadata.DoesNotExist:
            pass
