from django.conf import settings
from django.utils import timezone
from requests.adapters import HTTPAdapter, Retry
from urllib3.exceptions import LocationParseError, MaxRetryError
from bcmr_main.models import *
from dateutil import parser
from datetime import datetime
import pytz
import random
import requests
import hashlib
import logging

LOGGER = logging.getLogger(__name__)


def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.utc)


def decode_str(encoded_string):
    try:
        return bytearray.fromhex(encoded_string).decode()
    except UnicodeDecodeError as ude:
        return ''
    except ValueError:
        return ''


def encode_str(raw_string):
    binary_content = bytearray()
    binary_content.extend(raw_string.encode())
    hasher = hashlib.sha256(binary_content)
    return hasher.hexdigest()


def decode_url(encoded_url):
    decoded_bcmr_url = decode_str(encoded_url)
    if '.' in decoded_bcmr_url:
        if not decoded_bcmr_url.startswith('https://'):
            decoded_bcmr_url = 'https://' + decoded_bcmr_url
    else:
        if not decoded_bcmr_url.startswith('ipfs://'):
            decoded_bcmr_url = 'ipfs://' + decoded_bcmr_url
    return decoded_bcmr_url


def _request_url(url):
    response = None
    try:
        session = requests.Session()
        retry_triggers = tuple( x for x in requests.status_codes._codes if x not in [200, 301, 302, 307, 308, 404])
        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=retry_triggers)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        LOGGER.info('Downloading from: ' + url)
        response = session.get(url, timeout=30)
    except MaxRetryError:
        pass
    except requests.exceptions.RetryError:
        pass
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.InvalidURL:
        pass
    except LocationParseError:
        pass
    except Exception as e:
        pass
    return response


def download_url(url):
    response = None
    ipfs_cid = None 

    if url.startswith('ipfs://'):
        ipfs_cid = url.split('ipfs://')[1]

    # Temporarily use other gateway for nftstorage.link
    if url.startswith('https://nftstorage.link/ipfs') or url.startswith('nftstorage.link/ipfs'):
        ipfs_cid_index = url.index('ipfs') + 5 
        ipfs_cid = url[ipfs_cid_index:]

    if ipfs_cid:
        ipfs_gateways = [
            "ipfs.paytaca.com",
            # "w3s.link",
            # "nftstorage.link",
            # "cf-ipfs.com",
            # "cloudflare-ipfs.com",
            # "ipfs-gateway.clud",
            # "ipfs.filebase.io"
        ]
        # random.shuffle(ipfs_gateways)
        for ipfs_gateway in ipfs_gateways:
            final_url = f'https://{ipfs_gateway}/ipfs/{ipfs_cid}'
            if ipfs_gateway == 'cashtokens-studio.mypinata.cloud':
                final_url += f'?pinataGatewayToken={settings.PINATA_GATEWAY_TOKEN}'
            response = _request_url(final_url)
            if response and response.status_code == 200:
                break
    else:
        response = _request_url(url)
    return response


def send_webhook_token_update(category, index, txid, commitment=None, capability=None):
    if settings.WATCHTOWER_WEBHOOK_URL:
        token = Token.objects.get(
            category=category,
            commitment=commitment,
            capability=capability
        )
        info_dict = {
            'index': index,
            'txid': txid,
            'category': category,
            'is_nft': token.is_nft,
            'commitment': commitment,
            'capability': capability
        }

        url = f'{settings.WATCHTOWER_WEBHOOK_URL}/webhook/'
        _ = requests.post(url, json=info_dict)


def save_token(
    txid,
    category,
    amount,
    commitment=None,
    capability=None,
    is_nft=False,
    date_created=None
):
    token, created = Token.objects.get_or_create(
        category=category,
        commitment=commitment,
        capability=capability
    )
    if created:
        token.amount = amount
        token.debut_txid = txid
        token.date_created = date_created
        token.is_nft = is_nft
    token.save()


def save_output(
    txid,
    block,
    address,
    authbase=False,
    genesis=False,
    spender=None,
    identities=None,
    date=None
):
    output, created = IdentityOutput.objects.get_or_create(txid=txid)

    # used get or create only on txid & category, for the case of using the rescan_cashtoken_blocks script for existing txns
    output.block = block
    output.address = address
    output.authbase = authbase
    output.genesis = genesis
    output.identities = identities
    output.date = date

    if spender:
        output.spender = IdentityOutput.objects.get(txid=spender)
        output.spent = True

    output.save()

def save_ownership(
    category,
    txid,
    address,
    amount,
    spends
):
    pass


def fetch_authchain_length_from_chaingraph(token_id):
    url = 'https://gql.chaingraph.pat.mn/v1/graphql'
    headers = {
        'Content-Type': 'application/json',
    }
    query = """query {transaction(where:{hash:{_eq:\"\\\\x%s\"}}){hash authchains{authhead{hash},authchain_length}}}""" % token_id
    body = {
        'operationName': None,
        'variables': {},
        'query': query,
    }

    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code != 200:
        return print(f'Error {response.status_code} getting authchain of {token_id}')
    
    response = response.json()

    return response['data']['transaction'][0]['authchains'][0]['authchain_length']
    

def fetch_authchain_from_chaingraph(token_id, sort='asc', offset=0):
  """
  Fetches the authchain of the token_id from chaingraph
  Args:
    token_id (str): A string representing the token ID.
  Returns:
    list: The authchain, with index 0 = the authbase and last index = authhead
  """

  url = 'https://gql.chaingraph.pat.mn/v1/graphql'
  headers = {
      'Content-Type': 'application/json',
  }
  query = """{transaction(where:{hash:{_eq:\"\\\\x%s\"}}){hash authchains{authhead{hash}, authchain_length migrations(order_by:{migration_index:%s}, offset:%s){transaction{hash inputs(where:{outpoint_index:{_eq:\"0\"}}){outpoint_index}outputs{output_index locking_bytecode}}}}}}""" % (token_id, sort, offset)
  body = {
      'operationName': None,
      'variables': {},
      'query': query,
  }

  response = requests.post(url, headers=headers, json=body)
  
  if response.status_code != 200:
    return print(f'Error {response.status_code} getting authchain of {token_id}')
  
  response = response.json()
  authchain = []
  migrations = None
  
  try:
    migrations = response['data']['transaction'][0]['authchains'][0]['migrations']
  except KeyError as e:
    LOGGER.info(f'Error @fetch_authchain_from_chaingraph no migrations found for {token_id}')
    LOGGER.info(e)  
  
  if migrations:
    authchain = list(map(lambda x: x['transaction'][0]['hash'].replace('\\x',''), migrations))
  return authchain


def fetch_authhead_from_chaingraph(token_id):
    url = 'https://gql.chaingraph.pat.mn/v1/graphql'
    headers = {
        'Content-Type': 'application/json',
    }
    query = """query {transaction(where:{hash:{_eq:"\\\\x%s"}}){hash authchains{authhead{hash,identity_output{fungible_token_amount}},authchain_length}}}""" % token_id
    body = {
        'operationName': None,
        'variables': {},
        'query': query,
    }

    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code != 200:
        return LOGGER.info(f'Error {response.status_code} getting authhead of {token_id}')
    
    response = response.json()
    authhead = None

    try:
        authhead = response['data']['transaction'][0]['authchains'][0]['authhead']
        if authhead:
            authhead = authhead['hash'].replace('\\x','')
    except KeyError as e:
        LOGGER.info(e)
    
    return authhead

def fetch_authchain_pub_from_chaingraph(token_id, sort='asc', offset=0):
    """
    Fetches chain of publications only.
    """
    url = 'https://gql.chaingraph.pat.mn/v1/graphql'
    headers = {
        'Content-Type': 'application/json',
    }
    
    op = "6a04%"
    query = """query {transaction(where:{hash:{_eq:\"\\\\x%s\"}}){hash authchains{authhead{hash}, authchain_length migrations(where: {transaction: {outputs: {locking_bytecode_pattern: { _like: \"%s\" }}}},order_by:{migration_index:%s},offset: %s){transaction{hash inputs(where:{outpoint_index:{_eq:"0"}}){outpoint_index}outputs(where: { locking_bytecode_pattern: { _like: \"%s\" } }){output_index locking_bytecode}}}}}}""" % (token_id, op, sort, offset, op)
    body = {
        'operationName': None,
        'variables': {},
        'query': query,
    }

    response = requests.post(url, headers=headers, json=body)
  
    if response.status_code != 200:
        return print(f'Error {response.status_code} getting authchain of {token_id}')
    
    response = response.json()
    authchain = []
    migrations = None

    try:
        migrations = response['data']['transaction'][0]['authchains'][0]['migrations']
    except KeyError as e:
        LOGGER.info(f'Error @fetch_authchain_pub_from_chaingraph no migrations found for {token_id}')
        LOGGER.info(e)
    
    if migrations:
        authchain = list(map(lambda x: x['transaction'][0]['hash'].replace('\\x',''), migrations))
    return authchain

def is_authhead(token_id, identity_output_txid):
    authhead = fetch_authhead_from_chaingraph(token_id)
    return (identity_output_txid == authhead, authhead )


