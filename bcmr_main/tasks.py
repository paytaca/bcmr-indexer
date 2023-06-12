from django.db.models import Q

from celery import shared_task

from bcmr_main.authchain import *
from bcmr_main.op_return import *
from bcmr_main.bchn import BCHN
from bcmr_main.models import *
from bcmr_main.utils import timestamp_to_date

import logging


LOGGER = logging.getLogger(__name__)



def generate_token_identity(token_data):
    token_identity = ''
    token_identity += token_data.get('category', '')
    token_identity += token_data.get('nft', {}).get('capability', '')
    token_identity += token_data.get('nft', {}).get('commitment', '')
    return token_identity


@shared_task(queue='process_tx')
def process_tx(tx_hash, block_txns=None):
    LOGGER.info(f'PROCESSING TX --- {tx_hash}')

    bchn = BCHN()
    tx = bchn._get_raw_transaction(tx_hash)

    block = None
    time = None
    if 'blockhash' in tx.keys():
        block = bchn.get_block_height(tx['blockhash'])
    if 'time' in tx.keys():
        time = timestamp_to_date(tx['time'])

    inputs = tx['vin']
    outputs = tx['vout']
    identity_input = inputs[0]
    identity_output = outputs[0]

    if 'coinbase' in identity_input.keys():
        return

    parsed_tx = bchn._parse_transaction(tx, include_outputs=False)
    input_token_identities = []
    input_txids = []
    for tx_input in parsed_tx['inputs']:

        # get a list of input txids that are potential identity outputs spends
        if tx_input['spent_index'] == 0:
            input_txids.append(tx_input['txid'])
        
        # track token identities in inputs for saving token ownership transfers
        token_data = tx_input['token_data']
        if token_data:
            token_identity = generate_token_identity(token_data)
            input_token_identities.append(token_identity)
    
    # collect token outputs, and BCMR output
    token_outputs = []
    bcmr_op_ret = {}
    op_ret_str = ''
    output_token_identities = []
    for index, output in enumerate(outputs):
        scriptPubKey = output['scriptPubKey']
        output_type = scriptPubKey['type']

        if output_type in ['pubkeyhash', 'scripthash']:
            if 'tokenData' in output.keys():
                token_outputs.append(output)

                token_data = output['tokenData']
                token_identity = generate_token_identity(token_data)
                output_token_identities.append(token_identity)
                
                # TODO: save ownership records
                if token_identity in input_token_identities:
                    # scenario: token transfer
                    pass
                else:
                    # scenario: token minting or mutation
                    pass
        
        elif output_type == 'nulldata':
            asm = scriptPubKey['asm']
            op_ret_str = asm
            asm = asm.split(' ')

            if len(asm) >= 4:
                if asm[1] == '1380795202':
                    _hex = scriptPubKey['hex']
                    # TODO: validate hex here

                    bcmr_op_ret['txid'] = tx_hash
                    bcmr_op_ret['index'] = index
                    bcmr_op_ret['encoded_bcmr_json_hash'] = asm[2]
                    bcmr_op_ret['encoded_bcmr_url'] = asm[3]

    # TODO: catch token burning by checking which token identities
    # are present in inputs but not in outputs
    for token_id in input_token_identities:
        if token_id not in output_token_identities:
            # scenario: token burning
            pass

    if block_txns:
        ancestor_txns = set(input_txids).intersection(set(block_txns))
        if ancestor_txns:
            for ancestor_txn in ancestor_txns:
                traverse_authchain(tx_hash, ancestor_txn, block_txns)

    parents = IdentityOutput.objects.filter(txid__in=input_txids)

    # detect genesis
    genesis = False
    category = None
    input_zero_txid = inputs[0].get('txid')
    if token_outputs:
        token_categories = list(map(lambda x: x['tokenData']['category'], token_outputs))
        genesis = input_zero_txid in token_categories
        if genesis:
            category = input_zero_txid

    if parents.count() or genesis:

        if genesis:
            # save authbase tx
            authbase_tx = bchn._get_raw_transaction(category)
            output_data = {}
            output_data['block'] = block
            output_data['address'] = authbase_tx['vout'][0]['scriptPubKey']['addresses'][0]
            output_data['parent_txid'] = authbase_tx['vin'][0]['txid']
            output_data['txid'] = category
            output_data['authbase'] = True
            output_data['genesis'] = False
            output_data['spent'] = True
            save_output(**output_data)

        # save current identity output
        output_data = {
            'txid': tx_hash,
            'parent_txid': category,
            'block': block,
            'address': identity_output['scriptPubKey']['addresses'][0],
            'authbase': False,
            'spent': False,
            'genesis': genesis,
            'spender': None,
            'date': time
        }
        save_output(**output_data)

        # set parent output as spent and spent by this current output
        current_output = IdentityOutput.objects.get(txid=tx_hash)
        if parents.exists():
            parents.update(
                spent=True,
                spender=current_output
            )

        # for cases that BCHN returns a parent and a child txn on the same block,
        # we check if any previous children that was saved in DB has this current output's txid as its parent
        # if so, we mark the current output as spent and spender = that previously saved child (one only since parent_txid is unique)
        children = IdentityOutput.objects.filter(parent_txid=tx_hash)
        if children.exists():
            current_output = IdentityOutput.objects.get(txid=tx_hash)
            current_output.spent = True
            current_output.spender = children.first()
            current_output.save()


        # defaults to true for genesis outputs without op return yet and non-zero outputs
        if bcmr_op_ret:
            process_op_return(**{
                **bcmr_op_ret,
                'op_return': op_ret_str,
                'publisher': current_output,
                'date': time
            })


    # parse and save tokens
    for obj in token_outputs:
        # index = obj['n']
        token_data = obj['tokenData']
        category = token_data['category']
        capability = None
        commitment = None
        is_nft = 'nft' in token_data.keys()

        if is_nft:
            nft_data = token_data['nft']
            commitment = nft_data['commitment']
            capability = nft_data['capability']
            
        save_token(
            tx_hash,
            category,
            commitment=commitment,
            capability=capability,
            is_nft=is_nft,
            date_created=time
        )
        
        # send_webhook_token_update(
        #     category,
        #     index,
        #     tx_hash,
        #     commitment=commitment,
        #     capability=capability
        # )


def record_txn_dates(qs, bchn):
    for element in qs:
        if hasattr(element, 'txid'):
            tx = bchn._get_raw_transaction(element.txid)
                
            if 'time' in tx.keys():
                time = timestamp_to_date(tx['time'])
                if isinstance(element, Registry) or isinstance(element, Token):
                    element.date_created = time
                element.save()


@shared_task(queue='recheck_unconfirmed_txn_details')
def recheck_unconfirmed_txn_details():
    LOGGER.info('RECHECKING UNSAVED INFO OF UNCONFIRMED TXNS')
    
    bchn = BCHN()
    outputs = IdentityOutput.objects.filter(
        Q(block__isnull=True) |
        Q(date__isnull=True)
    )
    tokens = Token.objects.filter(date_created__isnull=True)
    registries = Registry.objects.filter(date_created__isnull=True)

    record_txn_dates(tokens, bchn)
    record_txn_dates(registries, bchn)

    for output in outputs:
        tx = bchn._get_raw_transaction(output.txid)

        if 'blockhash' in tx.keys():
            block = bchn.get_block_height(tx['blockhash'])
            output.block = block

        if 'time' in tx.keys():
            output.date = timestamp_to_date(tx['time'])

        output.save()
