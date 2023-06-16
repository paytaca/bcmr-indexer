from django.db.models.signals import post_save
from django.dispatch import receiver
from bcmr_main.models import Registry


@receiver(post_save, sender=Registry)
def validate_registry(sender, instance=None, created=False, **kwargs):
    if instance.validity_checks:
        validity_checks = instance.validity_checks
        is_valid = list(validity_checks.values()).count(True) == len(validity_checks.keys())
        Registry.objects.filter(id=instance.id).update(valid=is_valid)
