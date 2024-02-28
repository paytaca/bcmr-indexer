import redis
import json

from decouple import config
from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import Registry, Token
from rest_framework.views import APIView
from django.http import JsonResponse
import dateutil.parser
from operator import itemgetter
from dateutil.parser import parse as parse_datetime


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
        token = Token.objects.filter(category=category)
        if token.exists():
            response = {
                'category': category,
                'error': 'no valid metadata found'
            }
            nft_type_key = kwargs.get('type_key', '') # commitment
            
            client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
            cache_key = f'metadata:token:{category}'            
            if nft_type_key: 
                cache_key = f'metadata:token:{category}:{nft_type_key}'
            cached_response = client.get(cache_key)

            if cached_response:
                response = json.loads(cached_response)
            else:
                registry = Registry.objects.filter(contents__identities__has_key=category)
                if registry.exists():
                    r = registry.latest('id')
                    if r:
                        identity_snapshots = r.contents['identities'][category]
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
                            response = transform_to_paytaca_expected_format(identity_snapshot, nft_type_key)
                            client.set(cache_key, json.dumps(response), ex=(60 * 60 * 24))
        else:
            response = {
                'error': 'category not found'
            }
        return JsonResponse(response, safe=False)
