from celery import shared_task

from bcmr_main.utils import (
    decode_bcmr_op_url,
    send_webhook_token_update,
)
from bcmr_main.bchn import BCHN
from bcmr_main.models import *

from dateutil import parser
import logging
import requests
import hashlib


LOGGER = logging.getLogger(__name__)


def log_invalid_op_ret(txid, json_hash, bcmr_url_encoded):
    LOGGER.error('--- Invalid OP_RETURN data received ---\n\n')
    LOGGER.error(f'TXID: {txid}')
    LOGGER.error(f'BCMR-JSON Hash: {json_hash}')
    LOGGER.error(f'Encoded BCMR URL: {bcmr_url_encoded}')
    

def process_op_ret(
    txid,
    json_hash,
    bcmr_url_encoded,
    index,
    commitment='',
    capability=''
):
    decoded_url = decode_bcmr_op_url(bcmr_url_encoded)
    bcmr_url_decoded = 'https://' + decoded_url.strip()
    response = requests.get(bcmr_url_decoded)
    status_code = response.status_code
    
    if status_code == 200:
        bcmr = response.json()
        binary_content = bytearray()
        binary_content.extend(response.text.encode())
        hasher = hashlib.sha256(binary_content)
        bcmr_hash = hasher.hexdigest()

        if json_hash == bcmr_hash:
            identities = bcmr['identities']
            version = bcmr['version']
            latest_revision = parser.parse(bcmr['latestRevision'])
            registry_identity = bcmr['registryIdentity']

            for category, token_history in identities.items():
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
                    if 'nfts' in token_data_keys:
                        token.is_nft = True
                        token.nfts = token_data['nfts']
                
                if 'uris' in latest_metadata_keys:
                    if 'icon' in latest_metadata['uris']:
                        token.icon = latest_metadata['uris']['icon']

                token.updated_at = latest_timestamp
                token.save()

                send_webhook_token_update(
                    category,
                    index,
                    txid,
                    commitment=commitment,
                    capability=capability
                )

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
            
            return True
        else:
            log_invalid_op_ret(txid, json_hash, bcmr_url_encoded)
    else:
        LOGGER.info(f'Something\'s wrong in fetching BCMR --- {bcmr_url_decoded} - {status_code}')
    
    return False


@shared_task(queue='process_tx')
def process_tx(tx_hash):
    LOGGER.info(f'PROCESSING TX --- {tx_hash}')

    bchn = BCHN()
    tx = bchn._get_raw_transaction(tx_hash)

    block = None
    if 'blockhash' in tx.keys():
        block = bchn.get_block_height(tx['blockhash'])

    inputs = tx['vin']
    outputs = tx['vout']

    if 'coinbase' in inputs[0].keys():
        return

    input_txids = list(map(lambda i: i['txid'], inputs))
    identity_input = input_txids[0]
    token_outputs = []
    bcmr_op_ret = {}
    
    # collect all outputs that are tokens (including BCMR op return)
    for output in outputs:
        scriptPubKey = output['scriptPubKey']
        output_type = scriptPubKey['type']

        if output_type in ['pubkeyhash', 'scripthash']:
            if 'tokenData' in output.keys():
                token_outputs.append(output)
        
        elif output_type == 'nulldata':
            op_return = scriptPubKey['asm']
            op_rets = op_return.split(' ')

            if len(op_rets) == 4:
                accepted_BCMR_encoded_vals = [ '1380795202', '0442434d52' ]
                if op_rets[1] in accepted_BCMR_encoded_vals:
                    bcmr_op_ret['txid'] = tx_hash
                    bcmr_op_ret['json_hash'] = op_rets[2]
                    bcmr_op_ret['bcmr_url_encoded'] = op_rets[3]
    

    # parse and save identity outputs
    for obj in token_outputs:
        index = obj['n']
        token_data = obj['tokenData']
        is_nft = 'nft' in token_data.keys()

        category = token_data['category']
        capability = ''
        commitment = ''

        if is_nft:
            nft_data = token_data['nft']
            commitment = nft_data['commitment']
            capability = nft_data['capability']

        # defaults to true for genesis outputs without op return yet and non-zero outputs
        is_valid_op_ret = True
        genesis = False

        if index == 0:
            if bcmr_op_ret:
                is_valid_op_ret = process_op_ret(
                    bcmr_op_ret['txid'],
                    bcmr_op_ret['json_hash'],
                    bcmr_op_ret['bcmr_url_encoded'],
                    index,
                    commitment=commitment,
                    capability=capability
                )

            if category == identity_input:
                genesis = True
            
        if is_valid_op_ret:
            token, _ = Token.objects.get_or_create(category=category)
            token.is_nft = is_nft
            token.save()

            send_webhook_token_update(
                token.category,
                index,
                tx_hash,
                commitment=commitment,
                capability=capability
            )

            # if genesis:
            #     # save authbase tx
            #     authbase_tx_hash = identity_input
            #     IdentityOutput(
            #         tx_hash=authbase_tx_hash,
            #         block=block,
            #         token=token,
            #         authbase=True,
            #         spent=True
            #     ).save()

            #     # save genesis (for now)
            #     IdentityOutput(
            #         tx_hash=tx_hash,
            #         block=block,
            #         token=token,
            #         genesis=genesis
            #     ).save()


@shared_task(queue='recheck_output_blockheight')
def recheck_output_blockheight():
    LOGGER.info('RECHECKING UNSAVED BLOCKHEIGHTS OF OUTPUTS')
    
    bchn = BCHN()
    outputs = IdentityOutput.objects.filter(block__isnull=True)

    for output in outputs:
        tx = bchn._get_raw_transaction(output.tx_hash)

        if 'blockhash' in tx.keys():
            block = bchn.get_block_height(tx['blockhash'])
            output.block = block
            output.save()
