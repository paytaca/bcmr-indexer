from rest_framework.views import APIView
from rest_framework import status
from django.http import JsonResponse
from django.db.models import ExpressionWrapper, CharField, F, Q
from rest_framework.decorators import api_view
from bcmr_main.models import Registry
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry
from bcmr_main.tasks import reindex

@api_view(['GET'])
def get_contents(request, category):
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            return JsonResponse(bcmr.contents)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Registry not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)


@api_view(['GET'])
def get_token(request, category):
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            if bcmr.get_token():
                return JsonResponse(bcmr.get_token())
            else: 
                return JsonResponse({'error': 'Token not found'},status=404)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Registry not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)

@api_view(['GET'])
def get_uris(request, category):
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            if bcmr.get_uris():
                return JsonResponse(bcmr.get_uris())
            else: 
                return JsonResponse({'error': 'Uris not found'},status=404)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Registry not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)
    
@api_view(['GET'])
def get_icon_uri(request, category):
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)

            if bcmr.get_icon_uri():
                return JsonResponse(bcmr.get_icon_uri())
            else: 
                return JsonResponse({'error': 'Icon uri not found'},status=404)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Registry not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)
    
@api_view(['GET'])
def get_token_nft(request, category, commitment):
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            bcmr = BitcoinCashMetadataRegistry(registry.contents)
            if bcmr.get_nft(commitment):
                return JsonResponse(bcmr.get_nft(commitment))
            else:
                return JsonResponse({'error': f'Nft with commitment {commitment} not found'}, status=404)
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)

@api_view(['GET'])
def get_published_url(request, category):
    """
    The url published on the op_return
    """
    try:
        # registry = Registry.objects.filter(
        #             contents__contains={'registryIdentity': category}
        #         ).latest('id')
        # try another method
        cond1 = f'"category":"{category}"'
        cond2 = f'"category": "{category}"'
        registry = Registry.objects.annotate(
                contents_string=ExpressionWrapper(
                    F('contents'),
                    output_field=CharField()
                )
            ).filter(Q(contents_string__icontains=cond1) | Q(contents_string__icontains=cond2)).latest('id')
        if registry.contents:
            if registry.bcmr_url:
                return JsonResponse({'url': registry.bcmr_url})
            else:
                return JsonResponse({'url': ''})
        else: 
            return JsonResponse({'error': 'Registry identity found, but with no contents'}, status=404)
    
    except Registry.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)

@api_view(['GET'])
def reindex_token(request, category):
    try:
        reindex.delay(category)
        return JsonResponse({'success': 'Reindexing task queued.' }, status=200)
    except:
        return JsonResponse({'error': 'Bad request'}, status=400)