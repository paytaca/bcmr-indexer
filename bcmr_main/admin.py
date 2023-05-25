from django.contrib import admin

from bcmr_main.models import *


admin.site.site_header = 'Paytaca BCMR Admin'


class TokenAdmin(admin.ModelAdmin):
    list_display = [
        'category',
        'amount',
        'is_nft',
        'commitment',
        'capability',
        'updated_at',
        'bcmr_url',
    ]

class RegistryAdmin(admin.ModelAdmin):
    list_display = [
        'category',
        'latest_revision',
    ]

class IdentityOutputAdmin(admin.ModelAdmin):
    list_display = [
        'txid',
        'index',
        'address',
        'block',
        'authbase',
        'genesis',
        'spent',
        'token',
        'date_created',
    ]

admin.site.register(Token, TokenAdmin)
admin.site.register(Registry, RegistryAdmin)
admin.site.register(IdentityOutput, IdentityOutputAdmin)
