from django.conf import settings
from django.utils import timezone

from bcmr_main.models import *
from dateutil import parser
from datetime import datetime
import pytz
import requests
import hashlib


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
    if not decoded_bcmr_url.startswith('ipfs://'):
        decoded_bcmr_url = 'https://' + decoded_bcmr_url.strip()
    return decoded_bcmr_url


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
