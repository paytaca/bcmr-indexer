from celery import shared_task

from bcmr_main.authchain import *
from bcmr_main.op_return import *
from bcmr_main.bchn import BCHN
from bcmr_main.models import *

import logging


LOGGER = logging.getLogger(__name__)


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

    identity_input = inputs[0]
    identity_output = outputs[0]
    identity_input_txid = identity_input['txid']
    identity_input_index = identity_input['vout']

    token_outputs = []
    bcmr_op_ret = {}
    op_ret_str = ''
    
    # collect token outputs, and BCMR output
    for output in outputs:
        scriptPubKey = output['scriptPubKey']
        output_type = scriptPubKey['type']

        if output_type in ['pubkeyhash', 'scripthash']:
            if 'tokenData' in output.keys():
                token_outputs.append(output)
        
        elif output_type == 'nulldata':
            asm = scriptPubKey['asm']
            op_ret_str = asm
            asm = asm.split(' ')

            if asm[1] == '1380795202':
                _hex = scriptPubKey['hex']
                # TODO: validate hex here

                bcmr_op_ret['txid'] = tx_hash
                bcmr_op_ret['encoded_bcmr_json_hash'] = asm[2]
                bcmr_op_ret['encoded_bcmr_url'] = asm[3]


    parents = IdentityOutput.objects.filter(txid=identity_input_txid)
    if parents.exists():
        TOKEN_DATA = traverse_authchain(identity_input_txid)
    else:
        # dont record pure BCH identity outputs
        if not token_outputs: return
        TOKEN_DATA = token_outputs[0]['tokenData']
    

    # save identity output
    genesis = False
    category = TOKEN_DATA['category']
    
    if token_outputs:
        token_categories = list(map(lambda x: x['tokenData']['category'], token_outputs))
        genesis = identity_input_txid in token_categories
        if genesis:
            category = identity_input_txid
        
    output_data = {
        'txid': tx_hash,
        'block': block,
        'address': identity_output['scriptPubKey']['addresses'][0],
        'category': category,
        'authbase': False,
        'spent': False,
        'genesis': genesis,
        'spender': None
    }
    save_output(**output_data)

    if genesis:
        # save authbase tx
        output_data['spender'] = tx_hash
        output_data['txid'] = identity_input_txid
        output_data['authbase'] = True
        output_data['genesis'] = False
        output_data['spent'] = True
        save_output(**output_data)

    # set parent output as spent and spent by this current output
    if parents.exists():
        current_output = IdentityOutput.objects.get(txid=tx_hash)
        parents.update(
            spent=True,
            spender=current_output
        )


    # defaults to true for genesis outputs without op return yet and non-zero outputs
    is_valid_op_ret = True
    bcmr_url = None

    if bcmr_op_ret:
        is_valid_op_ret, bcmr_url = process_op_ret(**{
            **bcmr_op_ret,
            'op_return': op_ret_str,
            'category': TOKEN_DATA['category']
        })


    # parse and save identity outputs and tokens
    for obj in token_outputs:
        index = obj['n']
        token_data = obj['tokenData']
        address = obj['scriptPubKey']['addresses'][0]
        amount = int(token_data['amount'])
        category = token_data['category']
        capability = None
        commitment = None
        is_nft = 'nft' in token_data.keys()

        if is_nft:
            nft_data = token_data['nft']
            commitment = nft_data['commitment']
            capability = nft_data['capability']
            
        save_token(
            amount,
            category,
            commitment=commitment,
            capability=capability,
            bcmr_url=bcmr_url,
            is_nft=is_nft
        )
        
        send_webhook_token_update(
            category,
            index,
            tx_hash,
            commitment=commitment,
            capability=capability
        )


@shared_task(queue='recheck_output_blockheight')
def recheck_output_blockheight():
    LOGGER.info('RECHECKING UNSAVED BLOCKHEIGHTS OF OUTPUTS')
    
    bchn = BCHN()
    outputs = IdentityOutput.objects.filter(block__isnull=True)

    for output in outputs:
        tx = bchn._get_raw_transaction(output.txid)

        if 'blockhash' in tx.keys():
            block = bchn.get_block_height(tx['blockhash'])
            output.block = block
            output.save()
