from rest_framework import serializers

from django.conf import settings

from bcmr_main.models import Token


class IdentitySerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    uris = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = (
            'name',
            'description',
            'token',
            'status',
            'uris',
        )

    def get_uris(self, obj):
        if obj.icon:
            return {
                'icon': obj.icon
            }
        return {}

    def get_token(self, obj):
        result = {
            'category': obj.category,
            'symbol': obj.symbol,
            'decimals': obj.decimals 
        }

        if obj.is_nft:
            result['nfts'] = obj.nfts
        return result


class TokenSerializer(serializers.ModelSerializer):
    metadata_url = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = (
            'category',
            'name',
            'description',
            'symbol',
            'decimals',
            'icon',
            'updated_at',
            'is_nft',
            'nfts',
            'metadata_url',
        )

    def get_metadata_url(self, obj):
        url_addition = ''
        if settings.NETWORK == 'chipnet':
            url_addition = '-chipnet'

        return f'https://bcmr{url_addition}.paytaca.com/api/registries/{obj.category}/latest/'
