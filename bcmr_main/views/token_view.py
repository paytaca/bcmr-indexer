import redis
import json

from decouple import config
from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import Registry, Token
from bcmr_main.tasks import update_registry_and_nft_cache
from rest_framework.views import APIView
from django.http import JsonResponse
import dateutil.parser
from operator import itemgetter
from dateutil.parser import parse as parse_datetime
from bcmr_main.utils import transform_to_paytaca_expected_format

class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        token = Token.objects.filter(category=category)
        
        if not token.exists():
            return JsonResponse({'error': 'category not found'}, safe=False, status=404)
        
        response = {
            'category': category,
            'error': 'no valid metadata found'
        }

        is_nft = token[0].is_nft

        nft_type_key = kwargs.get('type_key', '') 
        
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        cache_key = f'metadata:token:{category}'            
        if nft_type_key: 
            cache_key = f'metadata:token:{category}:{nft_type_key}'
        cached_response = client.get(cache_key)

        if cached_response:
            response = json.loads(cached_response)
            update_registry_and_nft_cache.delay(category, nft_type_key)
        else:
            registry = Registry.objects.filter(contents__identities__has_key=category, publisher__identities__contains=[category])
            if registry.exists():
                r = registry.latest('publisher_id')
                if r:
                    identity_snapshots = r.contents['identities'][category]
                    
                    # Handle non-standard BCMR format where identity_snapshots is a list
                    if isinstance(identity_snapshots, list):
                        # If it's a list, take the first (and presumably only) item
                        if identity_snapshots:
                            identity_snapshot = identity_snapshots[0]
                            if identity_snapshot:
                                response, nft_type_key_exists = transform_to_paytaca_expected_format(identity_snapshot, nft_type_key, is_nft)
                                if nft_type_key:
                                    if nft_type_key_exists:
                                        client.set(f'metadata:token:{category}:{nft_type_key}', json.dumps(response), ex=(60 * 60 * 24))
                                    else:
                                        # Saving, the default token metadata of non existing key, but expire early
                                        client.set(f'metadata:token:{category}:{nft_type_key}', json.dumps(response), ex=(60 * 15))
                                else:
                                    client.set(f'metadata:token:{category}', json.dumps(response), ex=(60 * 60 * 24))
                    else:
                        # Standard BCMR format - dictionary with timestamp keys
                        snapshot_keys = identity_snapshots.keys()
                        snapshots = []
                        for snapshot_key in snapshot_keys:
                            try:
                                snapshots.append([snapshot_key, parse_datetime(snapshot_key)])
                            except dateutil.parser._parser.ParserError:
                                pass
                        snapshots.sort(key=itemgetter(1))
                        latest_key, history_date = snapshots[-1]
                        identity_snapshot = identity_snapshots[latest_key]
                        if identity_snapshot:
                            response, nft_type_key_exists = transform_to_paytaca_expected_format(identity_snapshot, nft_type_key, is_nft)
                            if nft_type_key:
                                if nft_type_key_exists:
                                    client.set(f'metadata:token:{category}:{nft_type_key}', json.dumps(response), ex=(60 * 60 * 24))
                                else:
                                    # Saving, the default token metadata of non existing key, but expire early
                                    client.set(f'metadata:token:{category}:{nft_type_key}', json.dumps(response), ex=(60 * 15))
                            else:
                                client.set(f'metadata:token:{category}', json.dumps(response), ex=(60 * 60 * 24))

        return JsonResponse(response, safe=False)
