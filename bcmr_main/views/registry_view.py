from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import redirect
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
                if registry.allow_hash_mismatch and registry.watch_for_changes:
                    url = registry.bcmr_url
                    if not url.endswith('.json'):
                        url = url.rstrip('/') + '/.well-known/bitcoin-cash-metadata-registry.json'
                    return redirect(url)
                else:
                    registry = token_metadata.registry
                    metadata = registry.contents
                    return JsonResponse(metadata)
        except TokenMetadata.DoesNotExist:
            pass
        
        return Response(status=status.HTTP_404_NOT_FOUND)
