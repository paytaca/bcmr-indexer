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
    token_identity += token_data.get('nft', {}).get('capability')
    token_identity += token_data.get('nft', {}).get('commitment')
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

    identity_input_txid = identity_input['txid']
    # identity_input_index = identity_input['vout']

    # track token identities in inputs for saving token ownership transfers
    parsed_tx = bchn._parse_transaction(tx, include_outputs=False)
    input_token_identities = []
    for tx_input in parsed_tx['inputs']:
        token_data = tx_input['token_data']
        if token_data:
            token_identity = generate_token_identity(token_data)
            input_token_identities.append(token_identity)
    
    # collect token outputs, and BCMR output
    token_outputs = []
    bcmr_op_ret = {}
    op_ret_str = ''
    output_token_identities = []
    for output in outputs:
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
                    bcmr_op_ret['encoded_bcmr_json_hash'] = asm[2]
                    bcmr_op_ret['encoded_bcmr_url'] = asm[3]

    # TODO: catch token burning by checking which token identities
    # are present in inputs but not in outputs
    for token_id in input_token_identities:
        if token_id not in output_token_identities:
            pass

    TOKEN_DATA = None
    parents = IdentityOutput.objects.filter(txid=identity_input_txid)

    if parents.exists():
        TOKEN_DATA = traverse_authchain(identity_input_txid)
    else:
        if token_outputs:
            TOKEN_DATA = token_outputs[0]['tokenData']

        if block_txns:
            if identity_input_txid in block_txns:
                TOKEN_DATA = traverse_authchain(identity_input_txid)

    # ignore txn if:
    # 1. no parent has been found in database AND
    # 2. no parent found in same block AND
    # 3. no token outputs found in txn
    if TOKEN_DATA is None:
        return

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
        'parent_txid': identity_input_txid,
        'block': block,
        'address': identity_output['scriptPubKey']['addresses'][0],
        'category': category,
        'authbase': False,
        'spent': False,
        'genesis': genesis,
        'spender': None,
        'date': time
    }
    save_output(**output_data)

    if genesis:
        # save authbase tx
        authbase_tx = bchn._get_raw_transaction(identity_input_txid)
        output_data['address'] = authbase_tx['vout'][0]['scriptPubKey']['addresses'][0]
        output_data['parent_txid'] = authbase_tx['vin'][0]['txid']
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
    is_valid_op_ret = True
    bcmr_url = None

    if bcmr_op_ret:
        is_valid_op_ret, bcmr_url = process_op_return(**{
            **bcmr_op_ret,
            'op_return': op_ret_str,
            'category': TOKEN_DATA['category'],
            'date': time
        })


    # parse and save identity outputs and tokens
    for obj in token_outputs:
        index = obj['n']
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
        
        send_webhook_token_update(
            category,
            index,
            tx_hash,
            commitment=commitment,
            capability=capability
        )


def record_txn_dates(qs, bchn):
    for element in qs:
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
