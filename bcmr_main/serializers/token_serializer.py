from rest_framework import serializers

from bcmr_main.models import Token


class TokenSerializer(serializers.ModelSerializer):
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
