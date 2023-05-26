from bcmr_main.utils import *

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
    encoded_bcmr_url
):
    decoded_bcmr_json_hash = decode_str(encoded_bcmr_json_hash)
    decoded_bcmr_url = decode_url(encoded_bcmr_url)

    response = requests.get(decoded_bcmr_url)
    status_code = response.status_code
    is_valid = False
    
    if status_code == 200:
        encoded_response_json_hash = encode_str(response.text)

        if decoded_bcmr_json_hash == encoded_response_json_hash:
            bcmr_json = response.json()
            identities = bcmr_json['identities']

            for category, token_history in identities.items():
                if type(token_history) is not dict:
                    continue

                timestamps = list(token_history.keys())
                timestamps.sort(key=lambda x: parser.parse(x))
                latest_timestamp = timestamps[-1]
                latest_metadata = token_history[latest_timestamp]

                # record the latest identity metadata only
                bcmr_json['identities'][category][latest_timestamp] = latest_metadata
                save_registry(category, bcmr_json)
            
            is_valid = True
        else:
            log_invalid_op_ret(txid, encoded_bcmr_json_hash, encoded_bcmr_url)
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {decoded_bcmr_url} - {status_code}')
    
    return is_valid, decoded_bcmr_url
