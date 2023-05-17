from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from bcmr_main.models import Token

import requests


@receiver(post_save, sender=Token)
def update_watchtower(sender, instance=None, created=False, **kwargs):
    info_dict = {
        'category': instance.category,
        'name': instance.name,
        'description': instance.description,
        'symbol': instance.symbol,
        'decimals': instance.decimals,
        'image_url': instance.icon
    }
    url = f'{settings.WATCHTOWER_WEBHOOK_URL}/webhook/'
    response = requests.post(url, json=info_dict)
