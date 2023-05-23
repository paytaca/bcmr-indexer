from django.conf import settings

from bcmr_main.models import Token

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
