from django.contrib import admin
from bcmr_main.metadata import generate_token_metadata
from bcmr_main.op_return import process_op_return
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


def _regenerate_metadata(modeladmin, request, queryset):
    for metadata in queryset:
        generate_token_metadata(metadata.registry)

_regenerate_metadata.short_description = "Re-generate metadata"

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

    actions = [ _regenerate_metadata ]

    def category(self, obj):
        return obj.token.category
    
    def is_nft(self, obj):
        return obj.token.is_nft
    
    is_nft.boolean = True
    
    def valid(self, obj):
        return obj.registry.valid
    
    valid.boolean = True


def _process_op_return(modeladmin, request, queryset):
    for registry in queryset:
        process_op_return(
            registry.txid,
            registry.index,
            registry.op_return,
            registry.publisher,
            registry.date_created
        )

_process_op_return.short_description = "Process OP_RETURN"

def _generate_token_metadata(modeladmin, request, queryset):
    for registry in queryset:
        generate_token_metadata(registry)

_generate_token_metadata.short_description = "Generate token metadata"


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

    actions = [
        _process_op_return,
        _generate_token_metadata
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
        'address',
        'identities'
    ]

    raw_id_fields = [
        'spender'
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
