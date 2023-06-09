from django.conf import settings
from django.utils import timezone

from bcmr_main.models import *
from dateutil import parser
import requests
import hashlib


def decode_str(encoded_string):
    try:
        return bytearray.fromhex(encoded_string).decode()
    except UnicodeDecodeError as ude:
        return ''


def encode_str(raw_string):
    binary_content = bytearray()
    binary_content.extend(raw_string.encode())
    hasher = hashlib.sha256(binary_content)
    return hasher.hexdigest()


def decode_url(encoded_url):
    decoded_bcmr_url = decode_str(encoded_url)
    if not decoded_bcmr_url.startswith('ipfs://'):
        decoded_bcmr_url = 'https://' + decoded_bcmr_url.strip()
    return decoded_bcmr_url


def send_webhook_token_update(category, index, txid, commitment=None, capability=None):
    token = Token.objects.get(category=category, commitment=commitment)
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


def save_registry(txid, category, json_data, op_ret, valid=False):
    Registry(
        txid=txid,
        category=category,
        metadata=json_data,
        valid=valid,
        op_return=op_ret
    ).save()


def save_token(
    amount,
    category,
    commitment=None,
    capability=None,
    bcmr_url=None,
    is_nft=False
):
    token, _ = Token.objects.get_or_create(
        category=category,
        commitment=commitment
    )
    token.bcmr_url = bcmr_url
    token.amount = amount
    token.capability = capability
    token.is_nft = is_nft
    token.save()


def save_output(
    txid,
    block,
    address,
    category,
    authbase=False,
    genesis=False,
    spent=False,
    spender=None
):
    output, created = IdentityOutput.objects.get_or_create(txid=txid)

    # used get or create only on txid & category, for the case of using the rescan_cashtoken_blocks script for existing txns
    output.block = block
    output.address = address
    output.category = category
    output.authbase = authbase
    output.genesis = genesis
    output.spent = spent

    if spender:
        output.spender = IdentityOutput.objects.get(txid=spender)

    if not created:
        output.date_created = timezone.now()
    output.save()


def parse_token_info(category, type_key=None):
    info = {
        'name': '',
        'description': '',
        'symbol': '',
        'decimals': 0,
        'uris': { 'icon': '' },
        'types': None
    }

    registries = Registry.objects.filter(category=category)
    if not registries.exists():
        raise Registry.DoesNotExist

    registry = registries.first()

    if not registry.metadata:
        raise Registry.DoesNotExist
        
    identities = registry.metadata['identities']

    try:
        identities = identities[category] # category key
    except KeyError as ke:
        # for registries that have incorrect category used as key
        raise Registry.DoesNotExist

    # BCMR v2
    if isinstance(identities, dict):
        timestamps = []
        for timestamp in identities.keys():
            timestamps.append({
                'timestamp': timestamp
            })
        if timestamps:
            timestamps.sort(key=lambda x: parser.parse(x['timestamp']))
            latest_timestamp = timestamps[-1]
            metadata = identities[latest_timestamp['timestamp']]

    # BCMR v1
    if isinstance(identities, list):
        metadata = identities[0]

    token_data = metadata['token']
    token_data_keys = token_data.keys()
    metadata_keys = metadata.keys()

    if 'name' in metadata_keys:
        info['name'] = metadata['name']

    if 'description' in metadata_keys:
        info['description'] = metadata['description']

    if 'uris' in metadata_keys:
        uris = metadata['uris']
        if 'icon' in uris.keys():
            info['uris']['icon'] = uris['icon']

    if 'symbol' in token_data_keys:
        info['symbol'] = token_data['symbol']
    
    if 'decimals' in token_data_keys:
        info['decimals'] = token_data['decimals']

    if 'nfts' in token_data_keys:
        nfts = token_data['nfts']
        if 'parse' in nfts.keys():
            parse = nfts['parse']

            if type_key:
                info['types'] = {
                    type_key: parse['types'][type_key]
                }
            else:
                if 'types' in parse.keys():
                    info['types'] = list(parse['types'].keys())
                    
    return info
