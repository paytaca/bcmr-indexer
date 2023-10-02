from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Token, TokenMetadata


class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        type_key = kwargs.get('type_key', '')
        token = None
        try:
            if type_key:
                token = Token.objects.get(
                    category=category,
                    is_nft=True,
                    commitment=type_key,
                    capability='none'
                )
            else:
                token = Token.objects.get(
                    category=category,
                    is_nft=False
                )
        except Token.DoesNotExist:
            pass

        metadata = None
        if token:
            if type_key:
                token_metadata = TokenMetadata.objects.filter(
                    token=token,
                    metadata_type='type'
                ).order_by('date_created', 'registry_id').last()
            else:
                token_metadata = TokenMetadata.objects.filter(
                    token=token,
                    metadata_type='category'
                ).order_by('date_created', 'registry_id').last()  
            if token_metadata:
                metadata = token_metadata.contents
        
        if not metadata:
            token_metadata = TokenMetadata.objects.filter(
                token__category=category,
                metadata_type='category'
            ).order_by('date_created').last()
            if token_metadata:
                metadata = token_metadata.contents

        if metadata:
            # Check if token is NFT or not
            token_check = Token.objects.filter(category=category)
            if token_check.exists():
                token = token_check.first()
                metadata['is_nft'] = token.is_nft
            return JsonResponse(metadata)

        category_check = Token.objects.filter(category=category)
        if category_check.exists():
            response = {
                'category': category,
                'error': 'no valid metadata found'
            }
        else:
            response = {
                'error': 'category not found'
            }
        return JsonResponse(response)
