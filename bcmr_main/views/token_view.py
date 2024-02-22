import redis
import json

from decouple import config
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry
from cts.tasks import update_identity_snapshot_cache
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Token, TokenMetadata


# class TokenView(APIView):

#     def get(self, request, *args, **kwargs):
#         category = kwargs.get('category', '')
#         type_key = kwargs.get('type_key', '')
#         token = None
#         try:
#             if type_key:
#                 token = Token.objects.get(
#                     category=category,
#                     is_nft=True,
#                     commitment=type_key,
#                     capability='none'
#                 )
#             else:
#                 token = Token.objects.get(
#                     category=category,
#                     is_nft=False
#                 )
#         except Token.DoesNotExist:
#             pass

#         metadata = None
#         if token:
#             if type_key:
#                 token_metadata = TokenMetadata.objects.filter(
#                     token=token,
#                     metadata_type='type'
#                 ).order_by('date_created', 'registry_id').last()
#             else:
#                 token_metadata = TokenMetadata.objects.filter(
#                     token=token,
#                     metadata_type='category'
#                 ).order_by('date_created', 'registry_id').last()  
#             if token_metadata:
#                 metadata = token_metadata.contents
        
#         if not metadata:
#             token_metadata = TokenMetadata.objects.filter(
#                 token__category=category,
#                 metadata_type='category'
#             ).order_by('date_created').last()
#             if token_metadata:
#                 metadata = token_metadata.contents

#         if metadata:
#             # Check if token is NFT or not
#             token_check = Token.objects.filter(category=category)
#             if token_check.exists():
#                 token = token_check.first()
#                 metadata['is_nft'] = token.is_nft
#             return JsonResponse(metadata)

#         category_check = Token.objects.filter(category=category)
#         if category_check.exists():
#             response = {
#                 'category': category,
#                 'error': 'no valid metadata found'
#             }
#         else:
#             response = {
#                 'error': 'category not found'
#             }
#         return JsonResponse(response)

def transform_to_paytaca_expected_format(identity_snapshot, nft_type_key):
    if nft_type_key:
        if identity_snapshot.get('token') and identity_snapshot['token'].get('nfts'):
            nfts = identity_snapshot['token'].pop('nfts')
            if (nfts.get('parse') or {}).get('types' or {}).get(nft_type_key):
                identity_snapshot['type_metadata'] = nfts['parse']['types'][nft_type_key]
            identity_snapshot['is_nft'] = True
        else:
            identity_snapshot['is_nft'] = False
    
    return identity_snapshot

class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        nft_type_key = kwargs.get('type_key', '') # commitment
        include_token_nfts = True if request.query_params.get('include_token_nfts', '').lower() == 'true' else False
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        identity_snapshot = client.get(f'{category}_identity-snapshot_on_token_view')

        if identity_snapshot:
            identity_snapshot = json.loads(identity_snapshot)
            # Update cache every time it's touched
            client.set(f'{category}_identity-snapshot_on_token_view',json.dumps(identity_snapshot), ex=(60 * 30))
            return JsonResponse(transform_to_paytaca_expected_format(identity_snapshot, nft_type_key), safe=False)
        
        registry = Registry.find_registry_id(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                query_result = None
                if nft_type_key:
                    query_result = r.get_identity_snapshot_nft_type(category, nft_type_key)
                    if not query_result:
                        query_result = r.get_identity_snapshot_basic(category)
                else:
                    query_result = r.get_identity_snapshot_basic(category)

                if query_result and query_result.get('identity_snapshot'):
                    client.set(f'{category}_identity-snapshot_on_token_view',json.dumps(query_result['identity_snapshot']), ex=(60 * 30))
                    return JsonResponse(transform_to_paytaca_expected_format(query_result['identity_snapshot'], nft_type_key), safe=False)
                
        return JsonResponse(data=None, safe=False)
