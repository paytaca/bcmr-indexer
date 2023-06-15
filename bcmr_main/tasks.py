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
    zeroth_input_txids = []
    token_input_txids = []
    token_input_indices = []

    for tx_input in parsed_tx['inputs']:
        # get a list of input txids that are potential identity outputs spends
        if tx_input['spent_index'] == 0:
            zeroth_input_txids.append(tx_input['txid'])
        
        # track token identities in inputs for saving token ownership transfers
        token_data = tx_input['token_data']
        if token_data:
            token_input_indices.append(tx_input['spent_index'])
            token_input_txids.append(tx_input['txid'])
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


    if block_txns:
        ancestor_txns = set(zeroth_input_txids).intersection(set(block_txns))
        if ancestor_txns:
            for ancestor_txn in ancestor_txns:
                traverse_authchain(tx_hash, ancestor_txn, block_txns)

    parents = IdentityOutput.objects.filter(txid__in=zeroth_input_txids)

    # detect genesis
    genesis = False
    category = None
    input_zero_txid = inputs[0].get('txid')

    if token_outputs:
        token_categories = list(map(lambda x: x['tokenData']['category'], token_outputs))
        genesis = input_zero_txid in token_categories
        if genesis:
            category = input_zero_txid

    # parse and save tokens
    for obj in token_outputs:
        token_data = obj['tokenData']
        _category = token_data['category']
        capability = None
        commitment = None
        is_nft = 'nft' in token_data.keys()

        if is_nft:
            nft_data = token_data['nft']
            commitment = nft_data['commitment']
            capability = nft_data['capability']
        
        amount = None
        if token_data['amount']:
            amount = int(token_data['amount'])

        cashtoken = save_token(
            tx_hash,
            _category,
            amount,
            commitment=commitment,
            capability=capability,
            is_nft=is_nft,
            date_created=time
        )

        # save ownership records
        ownership, _ = Ownership.objects.get_or_create(
            txid=tx_hash,
            token=cashtoken,
            index=obj['n']
        )
        ownership.amount = amount
        ownership.value = obj['value'] * (10 ** 8)
        ownership.address = obj['scriptPubKey']['addresses'][0]
        ownership.date_acquired = time
        ownership.save()
        
        
    previous_ownerships = Ownership.objects.filter(
        txid__in=token_input_txids,
        index__in=token_input_indices
    )
    previous_ownerships.update(spent=True, spender=tx_hash)

    # scenario: token burning
    for idx, token_id in enumerate(input_token_identities):
        if token_id not in output_token_identities:
            burned_identities = Ownership.objects.filter(
                txid=token_input_txids[idx],
                index=token_input_indices[idx]
            )
            burned_identities.update(
                burned=True,
                burner=tx_hash
            )


    if parents.count() or genesis:
        if genesis:
            # save authbase tx
            authbase_tx = bchn._get_raw_transaction(category)
            output_data = {}
            output_data['block'] = block
            output_data['address'] = authbase_tx['vout'][0]['scriptPubKey']['addresses'][0]
            output_data['txid'] = category
            output_data['authbase'] = True
            output_data['genesis'] = False
            save_output(**output_data)

        # save current identity output
        recipient = ''
        if identity_output['scriptPubKey']['type'] == 'nulldata':
            recipient = 'nulldata'
        else:
            recipient = identity_output['scriptPubKey']['addresses'][0]
            
        output_data = {
            'txid': tx_hash,
            'block': block,
            'address': recipient,
            'authbase': False,
            'genesis': genesis,
            'spender': None,
            'date': time
        }
        save_output(**output_data)

        # set parent output as spent and spent by this current output
        current_output = IdentityOutput.objects.get(txid=tx_hash)
        parents.update(spent=True, spender=current_output)

        # defaults to true for genesis outputs without op return yet and non-zero outputs
        if bcmr_op_ret:
            process_op_return(**{
                **bcmr_op_ret,
                'op_return': op_ret_str,
                'publisher': current_output,
                'date': time
            })
        
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
                elif isinstance(element, Ownership):
                    element.date_acquired = time
                element.save()


@shared_task(queue='recheck_unconfirmed_txn_details')
def recheck_unconfirmed_txn_details():
    LOGGER.info('RECHECKING UNSAVED INFO OF UNCONFIRMED TXNS')
    
    bchn = BCHN()
    outputs = IdentityOutput.objects.filter(
        Q(block__isnull=True) |
        Q(date__isnull=True)
    )
    ownerships = Ownership.objects.filter(date_acquired__isnull=True)
    tokens = Token.objects.filter(date_created__isnull=True)
    registries = Registry.objects.filter(date_created__isnull=True)

    record_txn_dates(ownerships, bchn)
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
