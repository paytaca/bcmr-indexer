from rest_framework import serializers

from django.conf import settings

from bcmr_main.models import Token


class TokenSerializer(serializers.ModelSerializer):
    bcmr_url_mirror = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = (
            'category',
            'amount',
            'commitment',
            'capability',
            'is_nft',
            'bcmr_url', # link to original registry
            'bcmr_url_mirror',  # link to custom registry (contains only the latest metadata -- see tasks.py/process_op_ret)
            'updated_at',
        )

    def get_bcmr_url_mirror(self, obj):
        if obj.registry:
            url_addition = ''
            if settings.NETWORK == 'chipnet':
                url_addition = '-chipnet'

            return f'https://bcmr{url_addition}.paytaca.com/api/registries/{obj.category}/latest/'
        return None
