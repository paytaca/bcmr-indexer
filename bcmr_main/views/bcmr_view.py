from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry, TokenMetadata

from rest_framework.decorators import api_view
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry


@api_view(['GET'])
def get_token(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.get_token())
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse(status=404)
    except:
        return JsonResponse(status=400)
    

