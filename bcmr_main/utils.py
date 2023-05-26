from django.conf import settings
from django.utils import timezone

from bcmr_main.models import *

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


# without https://
def decode_url(encoded_url):
    decoded_bcmr_url = decode_str(encoded_url)
    decoded_bcmr_url = 'https://' + decoded_bcmr_url.strip()
    return decoded_bcmr_url


# def send_webhook_token_update(category, index, txid, commitment='', capability=''):
#     token = Token.objects.get(category=category)
#     info_dict = {
#         'index': index,
#         'txid': txid,
#         'category': token.category,
#         'name': token.name,
#         'description': token.description,
#         'symbol': token.symbol,
#         'decimals': token.decimals,
#         'image_url': token.icon,
#         'is_nft': token.is_nft,
#         'nft_details': token.nfts,
#         'commitment': commitment,
#         'capability': capability
#     }

#     url = f'{settings.WATCHTOWER_WEBHOOK_URL}/webhook/'
#     _ = requests.post(url, json=info_dict)


def save_registry(category, json_data):
    registry, _ = Registry.objects.get_or_create(category=category)
    registry.data = json_data
    registry.save()


def save_token(
    amount,
    category,
    commitment=None,
    capability=None,
    bcmr_url=None,
    is_nft=False
):
    try:
        registry = Registry.objects.get(category=category)
    except Registry.DoesNotExist as dne:
        registry = None

    token, _ = Token.objects.get_or_create(
        category=category,
        commitment=commitment
    )
    token.bcmr_url = bcmr_url
    token.amount = amount
    token.registry = registry
    token.capability = capability
    token.is_nft = is_nft
    token.save()


def save_output(
    txid,
    index,
    block,
    address,
    category,
    commitment=None,
    authbase=False,
    genesis=False,
    spent=False
):
    token = Token.objects.get(category=category, commitment=commitment)
    output, created = IdentityOutput.objects.get_or_create(
        txid=txid,
        index=index,
        token=token
    )
    # used get or create only on txid & index, for the case of using the rescan_cashtoken_blocks script for existing txns
    output.block = block
    output.address = address
    output.category = category
    output.authbase = authbase
    output.genesis = genesis
    output.spent = spent

    if not created:
        output.date_created = timezone.now()
    output.save()


def parse_token_info(category):
    try:
        info = {}
        registry = Registry.objects.get(category=category)
        identities = registry.metadata['identities']
        identities = identities[category] # category key
        metadata = identities[list(identities.keys())[0]] # timestamp keys

        info['name'] = metadata['name']
        info['description'] = metadata['description']

        token_data = metadata['token']
        token_data_keys = token_data.keys()

        if 'uris' in metadata.keys():
            uris = metadata['uris']
            if 'icon' in uris.keys():
                info['icon_url'] = uris['icon']

        if 'symbol' in token_data_keys:
            info['symbol'] = token_data['symbol']

        if 'nfts' in token_data_keys:
            nfts = token_data['nfts']

            if 'parse' in nfts.keys():
                parse = nfts['parse']

                if 'types' in parse.keys():
                    info['types'] = parse['types']
                    
        return info
    except Registry.DoesNotExist as dne:
        return {}
