from django.conf import settings
from django.utils import timezone

from bcmr_main.models import Token, IdentityOutput

from subprocess import Popen, PIPE
import requests


# OP_RETURN 'BCMR' <bcmr_json_hash> <encoded_bcmr_url>
def decode_bcmr_op_url(encoded_bcmr_url):
    cmd = f'node bcmr_main/js/decode_bcmr_op_url.js {encoded_bcmr_url}'
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    result = stdout.decode('utf8')
    return result


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
