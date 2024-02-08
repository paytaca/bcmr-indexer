from django.db.models.signals import post_save
from django.dispatch import receiver
from bcmr_main.models import Registry


@receiver(post_save, sender=Registry)
def parse(sender, instance=None, created=False, **kwargs):
    instance.contents
        
        