from bcmr_main.utils import *
from django.db import transaction
from bcmr_main.models import (
    Registry
)
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry
from jsonschema import ValidationError
from json.decoder import JSONDecodeError
from urllib.parse import urlparse
import logging
import json

LOGGER = logging.getLogger(__name__)

# Fields compared to decide whether a registry row actually needs saving.
# Watched registries are re-checked every 20 seconds; writing unchanged rows
# fires post_save signals which invalidate caches and rewrite the row forever.
_COMPARED_FIELDS = (
    'date_created',
    'op_return',
    'bcmr_url',
    'contents',
    'validity_checks',
    'bcmr_request_status',
)


def log_invalid_op_return(txid, encoded_bcmr_json_hash, hash_standards):
    LOGGER.error('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.error(f'TXID: {txid}')
    LOGGER.error(f'Encoded BCMR JSON Hash: {encoded_bcmr_json_hash}')
    LOGGER.error(f'COMPARED AGAINST: {str(hash_standards)}')


def _save_if_changed(registry_obj, original):
    changed = any(
        getattr(registry_obj, field) != original[field]
        for field in _COMPARED_FIELDS
    )
    if not changed:
        return False

    registry_obj.save()
    return True


def process_op_return(
    txid,
    index,
    op_return,
    publisher,
    date
):
    with transaction.atomic():
        op_return_split = op_return.split(' ')
        encoded_bcmr_json_hash = op_return_split[2]
        encoded_bcmr_url = op_return_split[3]

        decoded_bcmr_json_hash = decode_str(encoded_bcmr_json_hash)
        decoded_bcmr_url = decode_url(encoded_bcmr_url)

        # Double checking of <BCMR> OP_RETURN code
        if op_return.split(' ')[1] != '1380795202':
            return False, decoded_bcmr_url 

        registry_obj, _ = Registry.objects.get_or_create(
            txid=txid,
            index=index,
            publisher=publisher
        )

        original = {field: getattr(registry_obj, field) for field in _COMPARED_FIELDS}

        validity_checks = {
            'bcmr_file_accessible': None,
            'bcmr_hash_match': None,
            'identities_match': None
        }

        parsed_url = urlparse(decoded_bcmr_url)
        if parsed_url.scheme == 'https' and parsed_url.path == '':
            if 'ipfs.nftstorage.link' not in decoded_bcmr_url:
                decoded_bcmr_url = decoded_bcmr_url.rstrip('/') + '/.well-known/bitcoin-cash-metadata-registry.json'

        registry_obj.date_created = date
        registry_obj.op_return = op_return
        registry_obj.bcmr_url = decoded_bcmr_url
        registry_obj.validity_checks = validity_checks

        LOGGER.info(f'--URL: {decoded_bcmr_url}')

        response = download_url(decoded_bcmr_url)
        if not response:
            validity_checks['bcmr_file_accessible'] = False
            registry_obj.validity_checks = validity_checks
            _save_if_changed(registry_obj, original)

            return False, decoded_bcmr_url

        status_code = response.status_code

        registry_obj.bcmr_request_status = status_code

        validity_checks['bcmr_file_accessible'] = status_code == 200
        proceed = False
        if status_code == 200:
            if registry_obj.allow_hash_mismatch:
                proceed = True
            else:
                encoded_response_json_hash = encode_str(response.text)
                if encoded_response_json_hash in [decoded_bcmr_json_hash, encoded_bcmr_json_hash]:
                    validity_checks['bcmr_hash_match'] = True
                    proceed = True
                else:
                    validity_checks['bcmr_hash_match'] = False
                    proceed = False
                    log_invalid_op_return(txid, encoded_response_json_hash, [decoded_bcmr_json_hash, encoded_bcmr_json_hash])

                try:
                    BitcoinCashMetadataRegistry.validate_contents(response.text)
                    validity_checks['bcmr_format_valid'] = True
                    proceed = True
                except (JSONDecodeError, ValidationError):
                    validity_checks['bcmr_format_valid'] = False
                    proceed = False

            if proceed:
                try:
                    new_contents = json.loads(response.text)
                    if new_contents == registry_obj.contents:
                        LOGGER.info(
                            f'No changes for registry ID # {registry_obj.id}'
                        )
                    else:
                        LOGGER.info(
                            f'Saving content for registry ID # {registry_obj.id}'
                        )
                        registry_obj.contents = new_contents
                except json.decoder.JSONDecodeError:
                    pass
        else:
            LOGGER.info(f'Something\'s wrong in fetching BCMR --- {decoded_bcmr_url} - {status_code}')

        registry_obj.validity_checks = validity_checks
        _save_if_changed(registry_obj, original)

    return validity_checks, decoded_bcmr_url
