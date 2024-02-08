from rest_framework import serializers
from bcmr_main.models import *

class TokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Token
        fields = (
            'category',
            'commitment',
            'capability',
            'amount'
        )