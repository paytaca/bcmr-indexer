import redis
import json

from decouple import config
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry
from cts.tasks import update_identity_snapshot_cache
from ...registrycontenthelpers import get_identity_snapshot, get_identity_snapshot_basic

class IdentitySnapshot(APIView):
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):

        category = kwargs.get('category', '')
        include_token_nfts = True if request.query_params.get('include_token_nfts', '').lower() == 'true' else False
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        cache_key = f'identitysnapshot:{category}'
        identity_snapshot = client.get(cache_key)

        if identity_snapshot and not include_token_nfts:
            identity_snapshot = json.loads(identity_snapshot)
            # Update cache every time it's touched
            # Only cache basic IdentitySnapshot (without nfts)
            update_identity_snapshot_cache.delay(category)
            return JsonResponse(identity_snapshot, safe=False)
        
        # registry = Registry.find_registry_id(category)
        # if registry:
        #     r = Registry.objects.get(id=registry['registry_id'])
        #     if r:
        #         if include_token_nfts:
        #             identity_snapshot = r.get_identity_snapshot(category)
        #         else:
        #             identity_snapshot = r.get_identity_snapshot_basic(category)
        #             client.set(f'{category}_identity-snapshot',json.dumps(identity_snapshot), ex=(60 * 30))
        #         return JsonResponse(identity_snapshot, safe=False)
            
        # registry = Registry.find_registry_id(category)
        # if registry:
        #     r = Registry.objects.get(id=registry['registry_id'])
        #     if r:
        if include_token_nfts:
            identity_snapshot = get_identity_snapshot(category)
        else:
            identity_snapshot = get_identity_snapshot_basic(category)
            client.set(f'{category}_identity-snapshot',json.dumps(identity_snapshot), ex=(60 * 30))
        return JsonResponse(identity_snapshot, safe=False)
                
        # return JsonResponse(data=None, safe=False)
