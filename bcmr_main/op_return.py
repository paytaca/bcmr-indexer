from bcmr_main.utils import *
from bcmr_main.ipfs import *
from bcmr_main.models import Registry

from dateutil import parser
import requests
import logging


LOGGER = logging.getLogger(__name__)


def log_invalid_op_return(txid, encoded_bcmr_json_hash, encoded_bcmr_url):
    LOGGER.error('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.error(f'TXID: {txid}')
    LOGGER.error(f'Encoded BCMR JSON Hash: {encoded_bcmr_json_hash}')
    LOGGER.error(f'Encoded BCMR URL: {encoded_bcmr_url}')


def process_op_return(
    txid,
    encoded_bcmr_json_hash,
    encoded_bcmr_url,
    op_return,
    category,
    date
):
    decoded_bcmr_json_hash = decode_str(encoded_bcmr_json_hash)
    decoded_bcmr_url = decode_url(encoded_bcmr_url)

    # Double checking of <BCMR> OP_RETURN code
    if op_return.split(' ')[1] != '1380795202':
        return False, decoded_bcmr_url 

    registry_obj, _ = Registry.objects.update_or_create(
        txid=txid,
        category=category
    )
    registry_obj.date_created = date
    registry_obj.op_return = op_return
    registry_obj.bcmr_url = decoded_bcmr_url

    if decoded_bcmr_url.startswith('ipfs://'):
        response = download_ipfs_bcmr_data(decoded_bcmr_url)
    else:
        response = requests.get(decoded_bcmr_url)

    if not response:
        return False, decoded_bcmr_url

    status_code = response.status_code
    is_valid = False
    
    registry_obj.bcmr_request_status = status_code

    if status_code == 200:
        encoded_response_json_hash = encode_str(response.text)
        if (
            decoded_bcmr_json_hash == encoded_response_json_hash or  # bitcats (encoded before being hashed)
            encoded_bcmr_json_hash == encoded_response_json_hash     # matthieu wallet (simple hash of BCMR json, no prior encoding)
        ):
            is_valid = True
            registry_obj.valid = is_valid
        else:
            log_invalid_op_return(txid, encoded_bcmr_json_hash, encoded_bcmr_url)

        bcmr_json = response.json()
        registry_obj.metadata = bcmr_json
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {decoded_bcmr_url} - {status_code}')

    registry_obj.save()

    return is_valid, decoded_bcmr_url
