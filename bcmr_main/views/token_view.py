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
            token_metadata = TokenMetadata.objects.filter(token=token).order_by('date_created').last()
            if token_metadata:
                metadata = token_metadata.contents
        else:
            token_metadata = TokenMetadata.objects.filter(
                token__category=category,
                metadata_type='category'
            ).order_by('date_created').last()
            if token_metadata:
                metadata = token_metadata.contents

        if metadata:
            return JsonResponse(metadata)

        category_check = Token.objects.filter(category=category)
        if category_check.exists():
            response = {
                'category': category_check,
                'error': 'no valid metadata found'
            }
            return JsonResponse(response)
        return Response(status=status.HTTP_404_NOT_FOUND)
