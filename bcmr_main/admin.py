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
        'is_nft',
        'commitment',
        'capability',
        'date_created'
    ]

class RegistryAdmin(admin.ModelAdmin):
    search_fields = [
        'txid',
    ]
    list_display = [
        'txid',
        'index',
        'valid',
        'date_created',
    ]

class IdentityOutputAdmin(admin.ModelAdmin):
    search_fields = [
        'txid',
        'spender__txid',
        'block',
        'address'
    ]
    list_display = [
        'txid',
        'spender_txid',
        'block',
        'authbase',
        'genesis',
        'spent',
        'date',
        'address'
    ]

    def spender_txid(self, obj):
        if obj.spender:
            return obj.spender.txid
        return None
    

class BlockScanAdmin(admin.ModelAdmin):
    list_display = [
        'height',
        'transactions',
        'scanned',
        'scan_started',
        'scan_completed'
    ]


admin.site.register(Token, TokenAdmin)
admin.site.register(Registry, RegistryAdmin)
admin.site.register(IdentityOutput, IdentityOutputAdmin)
admin.site.register(BlockScan, BlockScanAdmin)
