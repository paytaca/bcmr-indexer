from django.db.models.signals import post_save
from django.dispatch import receiver
from bcmr_main.tasks import resolve_metadata
from bcmr_main.op_return import process_op_return
from bcmr_main.models import Registry, Token, TokenMetadata
from bcmr_main.utils import get_redis_client

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
    
@receiver(post_save, sender=Registry, dispatch_uid='clear_cache')
def clear_cache(sender, instance=None, created=False, **kwargs):
    categories = set()
    if instance.contents:
        authbases = list((instance.contents.get('identities') or {}).keys())
        for a in authbases:
            timestamps = list((instance.contents.get('identities').get(a) or {}).keys())
            for t in timestamps:
                category = (instance.contents.get('identities').get(a).get(t).get('token') or {}).get('category')
                if category:
                    categories.add(category)

    client = get_redis_client()
    keys_to_delete = []

    for c in categories:
        # Exact registry key (no wildcard suffix — the key has no sub-keys)
        keys_to_delete.append(f'registry:token:{c}')
        # Wildcard for any metadata sub-keys
        keys_to_delete += client.keys(f'metadata:token:{c}') + client.keys(f'metadata:token:{c}:*')

    # Also bust the txid:vout cache entry for this specific registry record
    if instance.txid and instance.index is not None:
        keys_to_delete.append(f'registry:{instance.txid}:{instance.index}')

    valid_keys = [k for k in keys_to_delete if k is not None]
    if valid_keys:
        client.delete(*valid_keys)
