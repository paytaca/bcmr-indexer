from rest_framework.views import APIView
from rest_framework import status
from django.http import JsonResponse
from rest_framework.decorators import api_view
from bcmr_main.models import Registry
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry

@api_view(['GET'])
def get_contents(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.contents)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse(status=404)
    except:
        return JsonResponse(status=400)


@api_view(['GET'])
def get_token(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.get_token() or {})
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse(status=404)
    except:
        return JsonResponse(status=400)

@api_view(['GET'])
def get_uris(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.get_uris() or {})
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse(status=404)
    except:
        return JsonResponse(status=400)
    
@api_view(['GET'])
def get_icon_uri(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.get_icon_uri() or '')
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse(status=404)
    except:
        return JsonResponse(status=400)
    
@api_view(['GET'])
def get_token_nft(request, category):
    try:
        registry = Registry.objects.filter(
                    contents__contains={'registryIdentity': category}
                ).latest('id')
        commitment = request.GET.get('commitment', None)
        
        if not commitment:
            return JsonResponse({'error': 'Missing "commitment" query parameter'}, status=400)
        
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            if bcmr.get_nft(commitment):
                return JsonResponse(bcmr.get_nft(commitment) or {})
            else:
                return JsonResponse({'error': f'Nft with commitment {commitment} not found'}, status=404)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)
    
