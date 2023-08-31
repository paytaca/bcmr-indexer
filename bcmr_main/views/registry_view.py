from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import TokenMetadata


class RegistryView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        try:
            token_metadata = TokenMetadata.objects.filter(
                token__category=category,
                metadata_type='category'
            ).latest('id')
            if token_metadata:
                registry = token_metadata.registry
                metadata = registry.contents
                metadata['$schema'] = 'https://cashtokens.org/bcmr-v2.schema.json'
                metadata['license'] = 'CC0-1.0'
                return JsonResponse(metadata)
        except TokenMetadata.DoesNotExist:
            pass
        
        return Response(status=status.HTTP_404_NOT_FOUND)
