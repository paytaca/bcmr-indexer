from celery import shared_task

from bcmr_main.utils import decode_bcmr_op_url
from bcmr_main.models import *

from dateutil import parser
import logging
import requests
import hashlib


LOGGER = logging.getLogger(__name__)


def log_invalid_op_ret(json_hash, bcmr_url_encoded):
    LOGGER.info('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.info(f'BCMR-JSON Hash: {json_hash}')
    LOGGER.info(f'Encoded BCMR URL: {bcmr_url_encoded}')


@shared_task(queue='process_op_return')
def process_op_return(category, json_hash, bcmr_url_encoded):
    decoded_url = decode_bcmr_op_url(bcmr_url_encoded)
    bcmr_url_decoded = 'https://' + decoded_url.strip()
    response = requests.get(bcmr_url_decoded)
    
    if response.status_code == 200:
        bcmr = response.json()
        hasher = hashlib.sha256(response.text.encode())
        bcmr_hash = hasher.hexdigest()

        if json_hash == bcmr_hash:
            identities = bcmr['identities']
            version = bcmr['version']
            latest_revision = parser.parse(bcmr['latestRevision'])
            registry_identity = bcmr['registryIdentity']

            for token_history in identities.values():
                timestamps = list(token_history.keys())
                timestamps.sort(key=lambda x: parser.parse(x))
                latest_timestamp = timestamps[-1]
                latest_metadata = token_history[latest_timestamp]

                token, _ = Token.objects.get_or_create(category=category)
                latest_metadata_keys = latest_metadata.keys()

                if 'name' in latest_metadata_keys:
                    token.name = latest_metadata['name']
                if 'description' in latest_metadata_keys:
                    token.description = latest_metadata['description']

                if 'token' in latest_metadata_keys:
                    token_data = latest_metadata['token']
                    token_data_keys = token_data.keys()

                    if 'symbol' in token_data_keys:
                        token.symbol = token_data['symbol']
                    if 'decimals' in token_data_keys:
                        token.decimals = token_data['decimals']
                
                if 'uris' in latest_metadata_keys:
                    if 'icon' in latest_metadata['uris']:
                        token.icon = latest_metadata['uris']['icon']
                
                if 'nfts' in latest_metadata_keys:
                    token.is_nft = True
                    token.nfts = latest_metadata['nfts']

                token.updated_at = latest_timestamp
                token.save()

                registry = Registry.objects.filter(token=token)

                if registry.exists():
                    registry = registry.first()
                    registry.version = version
                    registry.latest_revision = latest_revision
                    registry.registry_identity = registry_identity
                    registry.save()
                else:
                    Registry(
                        version=version,
                        latest_revision=latest_revision,
                        registry_identity=registry_identity,
                        token=token
                    ).save()
        else:
            log_invalid_op_ret(json_hash, bcmr_url_encoded)
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {bcmr_url_decoded} - {response.status_code}')
