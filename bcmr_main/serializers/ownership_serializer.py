from rest_framework import serializers

from bcmr_main.models import Ownership
from bcmr_main.serializers.token_serializer import TokenSerializer


class OwnershipSerializer(serializers.ModelSerializer):
    token = TokenSerializer()

    class Meta:
        model = Ownership
        fields = (
            'txid',
            'index',
            'address',
            'token',
            'amount',
            'value',
            'spent',
            'spender',
            'burned',
            'burner',
            'date_acquired',
        )
