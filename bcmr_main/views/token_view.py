import redis
import json

from decouple import config
from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import Registry
from rest_framework.views import APIView
from django.http import JsonResponse


def transform_to_paytaca_expected_format(identity_snapshot, nft_type_key):
    if nft_type_key:
        if identity_snapshot.get('token') and identity_snapshot['token'].get('nfts'):
            identity_snapshot['is_nft'] = True
            nfts = identity_snapshot['token'].pop('nfts')
            nft_type_details = (nfts.get('parse') or {}).get('types' or {}).get(nft_type_key)
            if nft_type_details: 
                identity_snapshot['type_metadata'] = nfts['parse']['types'][nft_type_key]
        else:
            identity_snapshot['is_nft'] = False
    else:
        if identity_snapshot.get('token') and identity_snapshot['token'].get('nfts'):
            identity_snapshot['token'].pop('nfts')
            identity_snapshot['is_nft'] = True
        else:
            identity_snapshot['is_nft'] = False

    if identity_snapshot.get('_meta'):
        identity_snapshot.pop('_meta')
    
    return identity_snapshot

class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        nft_type_key = kwargs.get('type_key', '') # commitment
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        
        cache_key = f'{category}_identity-snapshot_nft_type_on_token_view'
        
        if nft_type_key: 
            cache_key = f'{category}_identity-snapshot_nft_type_on_token_view_{nft_type_key}'

        ## Disable cache
        # identity_snapshot = client.get(f'{category}_identity-snapshot_nft_type_on_token_view')
        identity_snapshot = None ## Disable cache

        if identity_snapshot:
            identity_snapshot = json.loads(identity_snapshot)
            # Update cache every time it's touched
            # client.set(cache_key,json.dumps(identity_snapshot), ex=(60 * 30)) ## Disable cache
            return JsonResponse(transform_to_paytaca_expected_format(identity_snapshot, nft_type_key), safe=False)

        registry = Registry.find_registry_id(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                identity_snapshot = r.get_identity_snapshot(category)
                identity_snapshot = identity_snapshot.get('identity_snapshot')
                # identity_snapshot = None
                # if nft_type_key:
                #     identity_snapshot = r.get_identity_snapshot_nft_type(category, nft_type_key)
                #     if not identity_snapshot:
                #         identity_snapshot = r.get_identity_snapshot_basic(category)
                # else:
                #     identity_snapshot = r.get_identity_snapshot(category)

                if identity_snapshot:
                    # client.set(cache_key, json.dumps(identity_snapshot), ex=(60 * 30)) ## Disable cache
                    return JsonResponse(transform_to_paytaca_expected_format(identity_snapshot, nft_type_key), safe=False)
                
        return JsonResponse(data=None, safe=False)
