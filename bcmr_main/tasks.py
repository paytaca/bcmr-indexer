from django.db.models import Q
from django.conf import settings
from celery import shared_task
from django.db.models import Max
import simplejson as json
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


def _process_tx(tx, bchn):
    tx_hash = tx['txid']
    LOGGER.info(f'PROCESSING TX --- {tx_hash}')

    try:
        tx_obj = QueuedTransaction.objects.get(txid=tx_hash)
        tx = tx_obj.details
    except QueuedTransaction.DoesNotExist:
        tx_obj = QueuedTransaction(
            txid=tx_hash,
            details=tx
        )
        tx_obj.save()

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
        output['_event'] = ''
        scriptPubKey = output['scriptPubKey']
        output_type = scriptPubKey['type']

        if output_type in ['pubkeyhash', 'scripthash']:
            if 'tokenData' in output.keys():

                token_data = output['tokenData']
                token_identity = generate_token_identity(token_data)
                output['_identity'] = token_identity
                output_token_identities.append(token_identity)
                
                if token_identity in input_token_identities:
                    output['_event'] = 'transfer'

                token_outputs.append(output)

        
        elif output_type == 'nulldata':
            if not bcmr_op_ret:
                asm = scriptPubKey['asm']
                asm = asm.split(' ')

                if len(asm) >= 4:
                    if asm[1] == '1380795202':
                        op_ret_str = scriptPubKey['asm']
                        _hex = scriptPubKey['hex']
                        # TODO: validate hex here
                        bcmr_op_ret['txid'] = tx_hash
                        bcmr_op_ret['index'] = index

    # Catch token burning by checking which token identities
    # are present in inputs but not in outputs
    burned_tokens = []
    for token_identity in input_token_identities:
        if token_identity not in output_token_identities:
            # scenario: token burning
            burned_tokens.append(token_identity)

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

    # parse and save tokens
    for obj in token_outputs:
        token_data = obj['tokenData']
        category = token_data['category']
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

        token, created = save_token(
            tx_hash,
            category,
            amount,
            commitment=commitment,
            capability=capability,
            is_nft=is_nft,
            date_created=time
        )

        if created or obj['_event'] == 'transfer':
            acquisition_type = 'minting'
            # update/create ownership records
            if obj['_event'] == 'transfer':
                acquisition_type = 'transfer'
                ownership_check = Ownership.objects.filter(token=token, spent=False, burned=False)
                if ownership_check.exists():
                    latest_ownership = ownership_check.last()
                    latest_ownership.spent = True
                    latest_ownership.spender_txid = tx_hash
                    latest_ownership.save()

            _address = obj['scriptPubKey']['addresses'][0]
            ownership = Ownership(
                token=token,
                txid=tx_hash,
                index=obj['n'],
                address=_address,
                amount=amount,
                date_acquired=timezone.now(),
                acquired_via=acquisition_type
            )
            ownership.save()

        if obj['_identity'] in burned_tokens:
            latest_ownership = Ownership.objects.get(token=token, spent=False, burned=False)
            latest_ownership.spent = True
            latest_ownership.spender_txid = tx_hash
            latest_ownership.burned = True
            latest_ownership.save()

    if genesis:
        # save authbase tx
        authbase_tx = bchn._get_raw_transaction(category)
        output_data = {}
        output_data['block'] = block
        output_data['address'] = authbase_tx['vout'][0]['scriptPubKey']['addresses'][0]
        output_data['txid'] = category
        output_data['authbase'] = True
        output_data['genesis'] = False
        output_data['identities'] = [category]
        save_output(**output_data)

    if parents.count():
        print('---PARENTS FOUND:', [x.txid for x in parents])
        # save current identity output
        recipient = ''
        if identity_output['scriptPubKey']['type'] == 'nulldata':
            recipient = 'nulldata'
        else:
            recipient = identity_output['scriptPubKey']['addresses'][0]

        identities = []
        for _parent in parents:
            if _parent.identities:
                identities += list(_parent.identities)
        output_data = {
            'txid': tx_hash,
            'block': block,
            'address': recipient,
            'authbase': False,
            'genesis': genesis,
            'spender': None,
            'identities': list(set(identities)),
            'date': time
        }
        save_output(**output_data)

        # set parent output as spent and spent by this current output
        current_output = IdentityOutput.objects.get(txid=tx_hash)
        if parents.exists():
            for parent in parents:
                parent.spent = True
                parent.spender = current_output
                parent.save()

        # defaults to true for genesis outputs without op return yet and non-zero outputs
        if bcmr_op_ret:
            process_op_return(**{
                **bcmr_op_ret,
                'op_return': op_ret_str,
                'publisher': current_output,
                'date': time
            })


def _get_ancestors(tx, bchn=None, ancestors=[]):
    txid = tx['txid']
    try:
        tx_obj = QueuedTransaction.objects.get(txid=txid)
        tx = tx_obj.details
    except QueuedTransaction.DoesNotExist:
        tx_obj = QueuedTransaction(
            txid=txid,
            details=tx
        )
        tx_obj.save()

    if 'coinbase' in tx['vin'][0].keys():
        return ancestors[::-1]

    proceed = True

    # check if it matches a saved identity output
    identity_output_check = IdentityOutput.objects.filter(txid=txid)
    if identity_output_check.exists():
        proceed = False
    else:
        # check if tx is a token genesis
        first_input_txid = tx['vin'][0]['txid']
        for tx_out in tx['vout']:
            if 'tokenData' in tx_out.keys():
                if tx_out['tokenData']['category'] == first_input_txid:
                    ancestors.append(tx)
                    proceed = False
                    break

    # Limit recursion to up to 7 ancestors deep only
    # Anyway, in an exhaustive scan from the block height when cashtokens was
    # activated we only really need to look for the first ancestor to check
    # if it spends an identity output. Going 7 ancestors deep is just considered
    # here just in case any authbase identity outputs are somehow missed.
    if len(ancestors) >= 7:
        proceed = False

    if proceed:
        for tx_input in tx['vin']:
            if tx_input['vout'] == 0:
                # this is a potential identity output
                raw_tx_input = bchn._get_raw_transaction(tx_input['txid'])
                ancestors.append(raw_tx_input)
                return _get_ancestors(
                    raw_tx_input,
                    bchn,
                    ancestors
                )

    # return the ancestors list in reverse order
    return ancestors[::-1]


@shared_task(queue='process_tx')
def process_tx(tx):
    tx_hash = tx['txid']
    print('--- PROCESS TX:', tx_hash)

    if 'coinbase' in tx['vin'][0].keys():
        return

    bchn = BCHN()
    ancestor_txs = _get_ancestors(tx, bchn, [])
    tx_chain = ancestor_txs + [tx]
    print('-- CHAIN:', len(tx_chain))

    for txn in tx_chain:
        _process_tx(txn, bchn)


def record_txn_dates(qs, bchn):
    for element in qs:
        if hasattr(element, 'txid'):
            tx = bchn._get_raw_transaction(element.txid)
                
            if 'time' in tx.keys():
                time = timestamp_to_date(tx['time'])
                if isinstance(element, Registry) or isinstance(element, Token):
                    element.date_created = time
                element.save()


@shared_task(queue='celery_periodic_tasks')
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


@shared_task(queue='celery_periodic_tasks')
def resolve_metadata():
    registries = Registry.objects.filter(generated_metadata__isnull=True).order_by('date_created')
    for registry in registries:
        LOGGER.info(f'GENERATING METADATA FOR REGISRTY ID #{registry.id}')
        generate_token_metadata(registry)
        registry.generated_metadata = timezone.now()
        registry.save()
