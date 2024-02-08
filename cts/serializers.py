from rest_framework import serializers
from cts.models import *

class CashTokenSerializer(serializers.ModelSerializer):
        
    metadata = serializers.SerializerMethodField()

    def get_metadata(self, instance):
        request = self.context.get('request')
        if request and request.query_params and (request.query_params.get('include_metadata') or '').lower() == 'true':
            metadata = {}
            if instance.capability:
              metadata['nft'] = instance.nft_type    
            metadata['token'] = instance.token_category
            return metadata
        else: 
            return 'not_set'
        
    class Meta:
        model = CashToken
        fields = (
            'category',
            'commitment',
            'capability',
            'amount',
            'metadata'
        )