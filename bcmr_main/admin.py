from django.contrib import admin

from bcmr_main.models import *


admin.site.site_header = 'Paytaca BCMR Admin'


class TokenAdmin(admin.ModelAdmin):
    list_display = [
        'category',
        'name',
        'symbol',
        'decimals',
        'status',
        'is_nft',
        'updated_at',
    ]

class RegistryAdmin(admin.ModelAdmin):
    list_display = [
        'token',
        'latest_revision',
    ]

class IdentityOutputAdmin(admin.ModelAdmin):
    list_display = [
        'tx_hash',
        'block',
        'authbase',
        'genesis',
        'spent',
        'burned',
        'token',
        'date_created',
    ]

admin.site.register(Token, TokenAdmin)
admin.site.register(Registry, RegistryAdmin)
admin.site.register(IdentityOutput, IdentityOutputAdmin)
