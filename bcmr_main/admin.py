from django.contrib import admin

from bcmr_main.models import *


admin.site.site_header = 'Paytaca BCMR Admin'


class TokenAdmin(admin.ModelAdmin):
    search_fields = [
        'category',
        'txid',
    ]
    list_display = [
        'category',
        'txid',
        'is_nft',
        'commitment',
        'capability',
        'updated_at',
        'bcmr_url',
    ]

class RegistryAdmin(admin.ModelAdmin):
    search_fields = [
        'category',
        'txid',
    ]
    list_display = [
        'txid',
        'category',
        'valid',
        'date_created',
    ]

class IdentityOutputAdmin(admin.ModelAdmin):
    search_fields = [
        'parent_txid',
        'txid',
        'spender__txid',
        'block',
        'address',
        'category',
    ]
    list_display = [
        'parent_txid',
        'txid',
        'spender_txid',
        'block',
        'authbase',
        'genesis',
        'spent',
        'date',
        'address',
        'category',
    ]

    def spender_txid(self, obj):
        if obj.spender:
            return obj.spender.txid
        return None

admin.site.register(Token, TokenAdmin)
admin.site.register(Registry, RegistryAdmin)
admin.site.register(IdentityOutput, IdentityOutputAdmin)
