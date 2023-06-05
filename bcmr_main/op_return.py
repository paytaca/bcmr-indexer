from bcmr_main.utils import *
from bcmr_main.ipfs import *

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

    if encoded_bcmr_url.startswith('ipfs://'):
        response = download_ipfs_bcmr_data(decoded_bcmr_url)
    else:
        response = requests.get(decoded_bcmr_url)

    if not response:
        return False, decoded_bcmr_url

    status_code = response.status_code
    is_valid = False
    
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
    bcmrs = []
    
    if 'identities' in bcmr_json.keys():
        identities = bcmr_json['identities']

        for bcmr_category, token_history in identities.items():
            # exclude old identity schema versions
            if type(token_history) is not dict:
                continue

            timestamps = list(token_history.keys())
            timestamps.sort(key=lambda x: parser.parse(x))
            latest_timestamp = timestamps[-1]
            latest_metadata = token_history[latest_timestamp]
            bcmrs.append({
                'data': latest_metadata,
                'timestamp': latest_timestamp,
                'category': bcmr_category
            })
        
        if bcmrs:
            bcmrs.sort(key=lambda x: parser.parse(x['timestamp']))
            latest_identity = bcmrs[-1]
            latest_category = latest_identity['category']
            latest_timestamp = latest_identity['timestamp']
            latest_data = latest_identity['data']

            # record the latest identity metadata only
            bcmr_json['identities'][latest_category][latest_timestamp] = latest_data
            save_registry(
                txid,
                category,
                bcmr_json,
                op_return,
                valid=is_valid
            )
    
    return is_valid, decoded_bcmr_url
