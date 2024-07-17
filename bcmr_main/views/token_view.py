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


def transform_to_paytaca_expected_format(identity_snapshot, nft_type_key, is_nft):
    nft_type_key_exists = False
    if nft_type_key:
        if identity_snapshot.get('token') and identity_snapshot['token'].get('nfts'):
            nfts = identity_snapshot['token'].pop('nfts')
            if nft_type_key == 'empty' or nft_type_key == 'none':
                nft_type_key = ''
            nft_type_details = (nfts.get('parse') or {}).get('types' or {}).get(nft_type_key)
            if nft_type_details: 
                nft_type_key_exists = True
                identity_snapshot['type_metadata'] = nfts['parse']['types'][nft_type_key]

                # NOTE: This is a temporary fix for NFTs that do not have `image` field under `uris`
                # The `image` field is needed by Paytaca to display NFTs propery in the wallet
                type_uris = identity_snapshot['type_metadata']['uris']
                if 'asset' in type_uris.keys()  and 'image' not in type_uris.keys():
                    asset_uri = identity_snapshot['type_metadata']['uris']['asset']
                    asset_uri_ext = asset_uri.split('.')[-1].lower()
                    if asset_uri_ext in ['jpg', 'png', 'gif', 'svg']:
                        identity_snapshot['type_metadata']['uris']['image'] = asset_uri

                # For some collections that only specified an icon but not an image
                if 'icon' in type_uris.keys()  and 'image' not in type_uris.keys():
                    identity_snapshot['type_metadata']['uris']['image'] = identity_snapshot['type_metadata']['uris']['icon']
            
    if identity_snapshot.get('token') and identity_snapshot['token'].get('nfts'):
        identity_snapshot['token'].pop('nfts')

    if identity_snapshot.get('_meta'):
        identity_snapshot.pop('_meta')

    if identity_snapshot:
        identity_snapshot['is_nft'] = is_nft
    
    return (identity_snapshot, nft_type_key_exists)

class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        token = Token.objects.filter(category=category)
        
        if not token.exists():
            return JsonResponse({'error': 'category not found'}, safe=False)
        
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
        else:
            registry = Registry.objects.filter(contents__identities__has_key=category)
            if registry.exists():
                r = registry.latest('publisher_id')
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
