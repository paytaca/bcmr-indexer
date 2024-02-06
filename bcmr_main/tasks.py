

import time
import logging
import requests
import simplejson as json
from django.db.models import Q
from django.conf import settings
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry
from celery import shared_task
from django.db.models import Max
from jsonschema import ValidationError
from bcmr_main.op_return import *
from bcmr_main.bchn import BCHN
from bcmr_main.models import *
from bcmr_main.utils import timestamp_to_date
from bitcoinrpc.authproxy import AuthServiceProxy

LOGGER = logging.getLogger(__name__)

def validate_authhead(token_id, authhead_txid):
    chaingraph_url = 'https://gql.chaingraph.pat.mn/v1/graphql'
    authhead_query_template = """
        query {
        transaction(where: {
            hash: {
            _eq: "\\\\x%s"
            }
        }) {
            hash
            authchains {
            authhead {
                hash, identity_output {
                fungible_token_amount
                }
            },
            authchain_length
            }
        } 

        }
        """ % token_id
    
    retries = 0
    query_response = None
    time.sleep(1)
    while (retries < 3):
        res = requests.post(chaingraph_url, json={ 'query': authhead_query_template })
        if res.status_code == 200:
            LOGGER.info('JSON')
            LOGGER.info(res.json())
            query_response = res.json()
            return True
        retries += 1
        time.sleep(1)
    return False

    # {'data': {'transaction': [{'hash': '\\x60768cf071bacde07470b5b281b96d4fd98a94d9cbb90252a2a3c5ce78b056b2', 'authchains': [{'authhead': {'hash': '\\xf2813865b9865c763e361cc5a8828d2cf0579f68eaf3b3b3c335e73d3088d044', 'identity_output': [{'fungible_token_amount': '0'}]}, 'authchain_length': 16}]}]}}
    if query_response:
        transaction = query_response['data']['transaction']
        if transaction:
            authchains = transaction[0].get('authchains')
            if authchains:
                authhead = authchains[0].get('authhead').get('hash')
                if authhead:
                    LOGGER.info('AUTHHEAD')
                    LOGGER.info(authhead.replace('\\x',''))
                    return authhead_txid == authhead.replace('\\x','')
    return False

def extract_registry_pub_data(op_return_decoded_output: dict):
    """ 
    Extract registry publication data from the OP_RETURN 
    """
    if op_return_decoded_output['scriptPubKey']['type'] == 'nulldata' and op_return_decoded_output['scriptPubKey']['asm'].startswith('OP_RETURN'):
        asm_arr = op_return_decoded_output['scriptPubKey'].get('asm').split(' ') 
        
        if len(asm_arr) >= 4:  
            published_uris_string = bytes.fromhex(asm_arr[3]).decode('utf-8')
            return {
                'content_hash': asm_arr[2],
                'uris': published_uris_string.split(';')
            }
            

def load_registry(txid, decoded_txn, op_return_output):
    """
    Load the decoded op_return output to the Registry table
    """
    compute_hash = encode_str
    LOGGER.info('LOADING REGISTRY')
    if Registry.objects.filter(txid=txid).exists():
        return
    
    published_uris_and_content_hash = extract_registry_pub_data(op_return_output)
    LOGGER.info(published_uris_and_content_hash)
    if published_uris_and_content_hash:
        content_hash, uris = published_uris_and_content_hash.values()
        LOGGER.info(content_hash)
        LOGGER.info(uris)
        registry_contents = None
        published_uri = None
        response = None
        for uri in uris:
            LOGGER.info(msg=f'Found {uri}')
            if '.' in uri:
                if not uri.startswith('https://'):
                    uri = 'https://' + uri
                LOGGER.info(msg=f'Requesting registry from {uri}')
                response = requests.get(uri)
            else:
                if not uri.startswith('ipfs://'):
                    uri = 'ipfs://' + uri
                LOGGER.info(msg=f'Requesting registry from {uri}')
                response = download_ipfs_bcmr_data(uri)    
            if response.status_code == 200:
                LOGGER.info(msg=f'Requesting success from {uri}')
                registry_contents = response.text
                published_uri = uri
                break
        
        if registry_contents:
            # published_content_hash = ''
            # try:
            #     published_content_hash = bytes.fromhex(published_content_hash_hex).decode() 
            # except UnicodeDecodeError as e:
            #     published_content_hash = published_content_hash_hex.hex()
            ## for older bcmr publications

            validity_checks = {
                'bcmr_file_accessible': True,
                'bcmr_hash_match': content_hash == compute_hash(registry_contents),
                'identities_match': None
            }
            try:
                BitcoinCashMetadataRegistry.validate_contents(registry_contents)
                LOGGER.info('TOKEN CATEGORIESS')
                
            except ValidationError: 
                LOGGER.info('Validation Error')

            
            token_ids = BitcoinCashMetadataRegistry.get_token_categories(registry_contents)
            LOGGER.info('TOKEN IDS')
            LOGGER.info(token_ids)
            
            
            try:
                for token_id in token_ids:
                    if not validate_authhead(token_id, txid):
                        raise Exception(f'{txid} is not the authhead of {token_id}')
                    
                Registry.objects.get_or_create(
                    txid=txid,
                    op_return=op_return_output['scriptPubKey'].get('asm'),
                    defaults={
                        'txid': txid,
                        'index': op_return_output['n'],
                        'validity_checks': validity_checks,
                        'op_return': op_return_output['scriptPubKey'].get('asm'),
                        'bcmr_url': published_uri,
                        'contents': json.loads(registry_contents),
                        'bcmr_request_status': response.status_code
                    }
                )
            except Exception as e:
                LOGGER.info(msg='Registry get_or_create error')
                LOGGER.info(msg=e)
        

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

    # TODO: catch token burning by checking which token identities
    # are present in inputs but not in outputs
    for token_id in input_token_identities:
        if token_id not in output_token_identities:
            # scenario: token burning
            pass

    parents = IdentityOutput.objects.filter(txid__in=input_txids)

    # detect token genesis
    input_txids = [x.get('txid') for x in inputs if x.get('txid')]
    tokens_created = []  # list of category IDs
    for obj in token_outputs:
        token_data = obj['tokenData']
        category = token_data['category']

        if category in input_txids:
            tokens_created.append(category)
            
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

        save_token(
            tx_hash,
            category,
            amount,
            commitment=commitment,
            capability=capability,
            is_nft=is_nft,
            date_created=time
        )

    # save authbase tx
    if tokens_created:
        authbase_tx = bchn._get_raw_transaction(category)
        output_data = {}
        output_data['block'] = block
        output_data['address'] = authbase_tx['vout'][0]['scriptPubKey']['addresses'][0]
        output_data['txid'] = category
        output_data['authbase'] = True
        output_data['genesis'] = False
        output_data['identities'] = tokens_created
        save_output(**output_data)

    if parents.count():
        LOGGER.info(f'---PARENTS FOUND: {str([x.txid for x in parents])}')
        # save current identity output
        recipient = ''
        if identity_output['scriptPubKey']['type'] == 'nulldata':
            recipient = 'nulldata'
        else:
            recipient = identity_output['scriptPubKey']['addresses'][0]

        parent_identities = []
        for _parent in parents:
            if _parent.identities:
                parent_identities += list(_parent.identities)
        output_data = {
            'txid': tx_hash,
            'block': block,
            'address': recipient,
            'authbase': False,
            'genesis': len(tokens_created) > 0,
            'spender': None,
            'identities': list(set(parent_identities)),
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

    # In an exhaustive scan from the block height when cashtokens was
    # activated we only really need to look for the first ancestor to check
    # if it spends an identity output. Going 2 or more ancestors deep is just considered
    # in case any authbase identity outputs are somehow missed.
    if len(ancestors) >= 1:
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
def process_tx(tx=None, tx_hash=None):
    bchn = BCHN()
    if tx_hash:
        tx = bchn._get_raw_transaction(tx_hash)
    else:
        tx_hash = tx['txid']

    if 'coinbase' in tx['vin'][0].keys():
        return

    ancestor_txs = _get_ancestors(tx, bchn, [])
    tx_chain = ancestor_txs + [tx]
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


@shared_task(queue='resolve_metadata')
def resolve_metadata(registry_id=None):
    if registry_id:
        registries = Registry.objects.filter(id=registry_id)
    else:
        registries = Registry.objects.filter(generated_metadata__isnull=True).order_by('date_created')
    for registry in registries:
        LOGGER.info(f'GENERATING METADATA FOR REGISRTY ID #{registry.id}')
        generate_token_metadata(registry)
        registry.generated_metadata = timezone.now()
        registry.save()


@shared_task(queue='watch_registry_changes')
def watch_registry_changes():
    registries = Registry.objects.filter(watch_for_changes=True)
    for registry in registries:
        process_op_return(
            registry.txid,
            registry.index,
            registry.op_return,
            registry.publisher,
            registry.date_created
        )

        resolve_metadata.delay(registry.id)
        # generate_token_metadata(registry)

@shared_task(queue='mempool_worker_queue')
def process_op_return_from_mempool(raw_tx_hex:str):
    

    # x=requests.post('https://gql.chaingraph.pat.mn/v1/graphql', json={"query": body})

    rpc_connection = AuthServiceProxy(settings.BCHN_NODE)
    max_retries = 20
    retries = 0
    decoded_txn = None
    while retries < max_retries:
        try:
            LOGGER.info(f'@process_op_return_from_mempool: Trying to decode raw transaction')
            decoded_txn = rpc_connection.decoderawtransaction(raw_tx_hex)
            LOGGER.info('DECODED TRANSACTION')
            LOGGER.info(decoded_txn)
            break
        except Exception as exception:
            retries += 1
            if retries >= max_retries:
                LOGGER.info(f'@process_op_return_from_mempool: Error decoding raw hex tx')
                raise exception
            time.sleep(1)
    
    if decoded_txn:
        outputs = decoded_txn.get('vout')
        for output in outputs:
            if output['scriptPubKey']['type'] == 'nulldata' and output['scriptPubKey']['asm'].startswith('OP_RETURN'):
                # load_registry(decoded_txn['txid'], output)

                load_registry(decoded_txn['txid'], decoded_txn, output)

def _get_spender_tx(txid, index):
    url = 'https://watchtower.cash/api/transaction/spender/'
    resp = requests.post(url, json={'txid': txid, 'index': index})
    if resp.status_code == 200:
        data = resp.json()
        if data['tx_found']:
            if data['spent']:
                return data['spender']
    return None


@shared_task(queue='process_tx')
def retrace_authchain(token_id):
    LOGGER.info(f'CATEGORY: {token_id}')
    token_check = Token.objects.filter(category=token_id)
    if token_check.exists():
        token = token_check.earliest('id')
        txid = None
        try:
            LOGGER.info(f'GENESIS: {token.debut_txid}')
            identity_output = IdentityOutput.objects.get(txid=token.debut_txid, genesis=True)
            if identity_output.spender:
                LOGGER.info(f' |-- {identity_output.spender.txid}')
                txid = identity_output.spender.txid
                while txid:
                    txid = _get_spender_tx(txid, 0)
                    if txid:
                        LOGGER.info(f' |-- {txid}')
                        process_tx(tx_hash=txid)
                    else:
                        LOGGER.info('-- auth head reached --')

        except IdentityOutput.DoesNotExist:
            LOGGER.info('Identity output not found')
    else:
        LOGGER.info('Token not found')