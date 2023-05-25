from rest_framework import serializers

from django.conf import settings

from bcmr_main.models import Token


class TokenSerializer(serializers.ModelSerializer):
    original_bcmr_url = serializers.SerializerMethodField()
    paytaca_bcmr_url = serializers.SerializerMethodField()
    paytaca_bcmr_json = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = (
            'category',
            'amount',
            'commitment',
            'capability',
            'is_nft',
            'original_bcmr_url', # link to original registry
            'paytaca_bcmr_url',  # link to custom registry (contains only the latest metadata -- see tasks.py/process_op_ret)
            'paytaca_bcmr_json', # custom json metadata from paytaca_bcmr_url
            'updated_at',
        )

    def get_original_bcmr_url(self, obj):
        return obj.bcmr_url

    def get_paytaca_bcmr_json(self, obj):
        if obj.registry:
            return obj.registry.data
        return obj.registry

    def get_paytaca_bcmr_url(self, obj):
        if obj.registry:
            url_addition = ''
            if settings.NETWORK == 'chipnet':
                url_addition = '-chipnet'

            return f'https://bcmr{url_addition}.paytaca.com/api/registries/{obj.category}/latest/'
        return None
