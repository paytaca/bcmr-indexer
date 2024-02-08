from rest_framework import serializers
from .models import *


class TokenSerializer(serializers.ModelSerializer):

    nft_collection_type = serializers.Field()

    class Meta:
        model = NftParsingInformation
        fields = (
            'bytecode',
            'fields',
            'nft_collection_type'
        )
