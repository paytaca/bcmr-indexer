from django.contrib import admin

from bcmr_main.models import *


admin.site.site_header = 'Paytaca BCMR Admin'


class TokenAdmin(admin.ModelAdmin):

    search_fields = [
        'category'
    ]

    list_display = [
        'category',
        'is_nft',
        'commitment',
        'capability',
        'date_created'
    ]


class TokenMetadataAdmin(admin.ModelAdmin):

    search_fields = [
        'token__category'
    ]

    list_display = [
        'category',
        'is_nft',
        'valid',
        'contents'
    ]

    raw_id_fields = [
        'token',
        'registry',
        'identity',
    ]

    def category(self, obj):
        return obj.token.category
    
    def is_nft(self, obj):
        return obj.token.is_nft
    
    is_nft.boolean = True
    
    def valid(self, obj):
        return obj.registry.valid
    
    valid.boolean = True


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

    raw_id_fields = [
        'publisher'
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

    raw_id_fields = [
        'spender',
        'identities'
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


class OwnershipAdmin(admin.ModelAdmin):

    search_fields = [
        'address',
        'txid',
        'token__category',
    ]

    list_display = [
        'address',
        'txid',
        'index',
        'spent',
        'burned',
        'date_acquired',
    ]


admin.site.register(Token, TokenAdmin)
admin.site.register(TokenMetadata, TokenMetadataAdmin)
admin.site.register(Registry, RegistryAdmin)
admin.site.register(IdentityOutput, IdentityOutputAdmin)
admin.site.register(BlockScan, BlockScanAdmin)
admin.site.register(Ownership, OwnershipAdmin)
