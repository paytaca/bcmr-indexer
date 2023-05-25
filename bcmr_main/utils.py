from django.conf import settings
from django.utils import timezone

from bcmr_main.models import Token, IdentityOutput

import requests
import hashlib


def decode_str(encoded_string):
    return bytearray.fromhex(encoded_string).decode()


def encode_str(raw_string):
    binary_content = bytearray()
    binary_content.extend(raw_string.encode())
    hasher = hashlib.sha256(binary_content)
    return hasher.hexdigest()


def send_webhook_token_update(category, index, txid, commitment='', capability=''):
    token = Token.objects.get(category=category)
    info_dict = {
        'index': index,
        'txid': txid,
        'category': token.category,
        'name': token.name,
        'description': token.description,
        'symbol': token.symbol,
        'decimals': token.decimals,
        'image_url': token.icon,
        'is_nft': token.is_nft,
        'nft_details': token.nfts,
        'bcmr_json': token.bcmr_json,
        'bcmr_url': token.bcmr_url,
        'commitment': commitment,
        'capability': capability
    }

    url = f'{settings.WATCHTOWER_WEBHOOK_URL}/webhook/'
    _ = requests.post(url, json=info_dict)


def save_output(
    txid,
    index,
    block,
    address,
    category,
    authbase=False,
    genesis=False,
    spent=False
):
    token = Token.objects.get(category=category)
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
