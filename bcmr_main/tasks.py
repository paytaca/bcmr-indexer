from celery import shared_task

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

    input_txids = list(map(lambda i: i['txid'], inputs))
    identity_input_txid = input_txids[0]
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
            asm = scriptPubKey['asm']
            asm = asm.split(' ')

            if len(asm) == 4:
                is_bcmr_op_ret = False

                if asm[1] == '1380795202':
                    _hex = scriptPubKey['hex']
                    decoded_hex = decode_str(_hex)
                    validating_str = decoded_hex.split('@')[0]

                    # example script pubkey hex
                    # 6a0442434d5240303139643032616261633166393637353439663433653037306637323334383337326363333537643639363463663232616230663862346331623139636636383f697066732e7061742e6d6e2f697066732f516d665170724a7470696f4a6d53774c56545735684d445155734150686443327569727553786659707a47794a4e
                    if '\x04BCMR' in validating_str:
                        is_bcmr_op_ret = True

                if is_bcmr_op_ret:
                    bcmr_op_ret['txid'] = tx_hash
                    bcmr_op_ret['encoded_bcmr_json_hash'] = asm[2]
                    bcmr_op_ret['encoded_bcmr_url'] = asm[3]


    # defaults to true for genesis outputs without op return yet and non-zero outputs
    is_valid_op_ret = True
    bcmr_url = None
    
    if bcmr_op_ret:
        is_valid_op_ret, bcmr_url = process_op_ret(**bcmr_op_ret)


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

        genesis = False
        zeroth_output = index == 0

        if zeroth_output:
            if category == identity_input_txid:
                genesis = True
            
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

        if is_valid_op_ret:
            output_data = {
                'txid': tx_hash,
                'index': index,
                'block': block,
                'address': address,
                'category': category,
                'commitment': commitment,
                'authbase': False,
                'spent': False,
                'genesis': False
            }

            # save outputs that are one of the following:
                # = genesis (zeroth output with same token category as the zeroth input's txid)
                # = authbase (zeroth input with txid same as the token category of the zeroth output)
                # = neither above as long as
                #     - zeroth output (both ft and nft)
                #     - any index of nft output
            if genesis:
                # save genesis tx
                output_data['genesis'] = True
                save_output(**output_data)

                # save authbase tx
                output_data['txid'] = identity_input_txid
                output_data['authbase'] = True
                output_data['genesis'] = False
                output_data['spent'] = True
                save_output(**output_data)
            else:
                if zeroth_output or is_nft:
                    # save_output(**output_data)
                    # TODO: traverse authchain
                    pass


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
