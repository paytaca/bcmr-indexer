from bcmr_main.utils import *
from bcmr_main.ipfs import *
from bcmr_main.models import (
    Registry,
    # Token,
    #TokenMetadata
)
from bcmr_main.metadata import generate_token_metadata
# from django.utils import timezone
# from datetime import datetime
# from dateutil.parser import parse as parse_datetime
# from operator import itemgetter
from urllib3.exceptions import LocationParseError
import requests
import logging


LOGGER = logging.getLogger(__name__)


def log_invalid_op_return(txid, encoded_bcmr_json_hash, hash_standards):
    LOGGER.error('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.error(f'TXID: {txid}')
    LOGGER.error(f'Encoded BCMR JSON Hash: {encoded_bcmr_json_hash}')
    LOGGER.error(f'COMPARED AGAINST: {str(hash_standards)}')


def process_op_return(
    txid,
    index,
    op_return,
    publisher,
    date
):
    op_return_split = op_return.split(' ')
    encoded_bcmr_json_hash = op_return_split[2]
    encoded_bcmr_url = op_return_split[3]

    decoded_bcmr_json_hash = decode_str(encoded_bcmr_json_hash)
    decoded_bcmr_url = decode_url(encoded_bcmr_url)

    # Double checking of <BCMR> OP_RETURN code
    if op_return.split(' ')[1] != '1380795202':
        return False, decoded_bcmr_url 

    registry_obj, _ = Registry.objects.update_or_create(
        txid=txid,
        index=index,
        publisher=publisher
    )

    validity_checks = {
        'bcmr_file_accessible': None,
        'bcmr_hash_match': None,
        'identities_match': None
    }

    registry_obj.date_created = date
    registry_obj.op_return = op_return
    registry_obj.bcmr_url = decoded_bcmr_url
    registry_obj.validity_checks = validity_checks
    registry_obj.save()

    print('--URL:', decoded_bcmr_url)

    response = None
    try:
        if decoded_bcmr_url.startswith('ipfs://'):
            response = download_ipfs_bcmr_data(decoded_bcmr_url)
        else:
            response = requests.get(decoded_bcmr_url)
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.InvalidURL:
        pass
    except LocationParseError:
        pass
        
    if not response:
        validity_checks['bcmr_file_accessible'] = False
        registry_obj.validity_checks = validity_checks
        registry_obj.save()

        return False, decoded_bcmr_url

    status_code = response.status_code
    
    registry_obj.bcmr_request_status = status_code
    contents = None

    validity_checks['bcmr_file_accessible'] = status_code == 200
    if status_code == 200:
        encoded_response_json_hash = encode_str(response.text)
        # if (
        #     decoded_bcmr_json_hash == encoded_response_json_hash or  # bitcats (encoded before being hashed)
        #     encoded_bcmr_json_hash == encoded_response_json_hash     # matthieu wallet (simple hash of BCMR json, no prior encoding)
        # ):
        if encoded_response_json_hash in [decoded_bcmr_json_hash, encoded_bcmr_json_hash]:
            validity_checks['bcmr_hash_match'] = True
        else:
            validity_checks['bcmr_hash_match'] = False
            log_invalid_op_return(txid, encoded_response_json_hash, [decoded_bcmr_json_hash, encoded_bcmr_json_hash])
        try:
            contents = response.json()
            registry_obj.contents = contents
            registry_obj.save()
        except requests.exceptions.JSONDecodeError:
            pass
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {decoded_bcmr_url} - {status_code}')

    registry_obj.validity_checks = validity_checks
    registry_obj.save()

    return validity_checks, decoded_bcmr_url
