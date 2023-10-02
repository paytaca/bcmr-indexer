from django.contrib import admin
from crc20.models import Registry


class RegistryAdmin(admin.ModelAdmin):

    list_display = [
        'publisher',
        'bcmr_url',
        'last_updated'
    ]

    actions = [
        # download_registry
    ]
