from bcmr_main.utils import *
from bcmr_main.ipfs import *
from bcmr_main.models import Registry

from dateutil import parser
import requests
import logging


LOGGER = logging.getLogger(__name__)


def log_invalid_op_ret(txid, encoded_bcmr_json_hash, encoded_bcmr_url):
    LOGGER.error('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.error(f'TXID: {txid}')
    LOGGER.error(f'Encoded BCMR JSON Hash: {encoded_bcmr_json_hash}')
    LOGGER.error(f'Encoded BCMR URL: {encoded_bcmr_url}')


def process_op_ret(
    txid,
    encoded_bcmr_json_hash,
    encoded_bcmr_url,
    op_return,
    category
):
    decoded_bcmr_json_hash = decode_str(encoded_bcmr_json_hash)
    decoded_bcmr_url = decode_url(encoded_bcmr_url)

    registry_obj = Registry(
        txid=txid,
        category=category,
        op_return=op_return,
        bcmr_url=decoded_bcmr_url
    )
    registry_obj.save()

    if encoded_bcmr_url.startswith('ipfs://'):
        response = download_ipfs_bcmr_data(decoded_bcmr_url)
    else:
        response = requests.get(decoded_bcmr_url)

    if not response:
        return False, decoded_bcmr_url

    status_code = response.status_code
    is_valid = False
    
    registry_obj.bcmr_request_status = status_code
    registry_obj.save()

    if status_code == 200:
        encoded_response_json_hash = encode_str(response.text)

        if (
            decoded_bcmr_json_hash == encoded_response_json_hash or
            decoded_bcmr_json_hash == encoded_bcmr_json_hash
        ):
            is_valid = True
        else:
            log_invalid_op_ret(txid, encoded_bcmr_json_hash, encoded_bcmr_url)
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {decoded_bcmr_url} - {status_code}')

    bcmr_json = response.json()
    registry_obj.metadata = bcmr_json
    registry_obj.save()

    return is_valid, decoded_bcmr_url
