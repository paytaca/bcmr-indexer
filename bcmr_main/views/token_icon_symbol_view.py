from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry
from bcmr_main.models import Token, TokenMetadata
from jsonschema import ValidationError

class TokenIconSymbolView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        token = None

        
        try:
          token = Token.objects.get(
            category=category
          )
        except Token.DoesNotExist:
          response = {
                'error': 'category not found'
            }

        contents = None
        if token:
            token_metadata = TokenMetadata.objects.filter(token=token).order_by('date_created', 'registry_id').last()
            if token_metadata:
                contents = token_metadata.contents
        if contents:
          bcmr = BitcoinCashMetadataRegistry(contents)
          try:
            bcmr.validate(contents)
            response = { 'category': category, 'icon_uri': bcmr.get_icon_uri(), 'symbol': bcmr.get_symbol()}
          except ValidationError:
            # TODO check if we can still return the icon or symbol even if bcmr fails validation 
            response = {'error': 'bcmr is invalid'}

        return JsonResponse(response)
