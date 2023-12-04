import requests
import random
import logging

LOGGER = logging.getLogger(__name__)
MAX_RETRIES = 3


def download_ipfs_bcmr_data(ipfs_url):
    ipfs_cid = ipfs_url.split('ipfs://')[1]
    ipfs_gateways = [
        "cloudflare-ipfs.com",
        "ipfs-gateway.cloud",
        "ipfs.filebase.io",
        "nftstorage.link",
        "gateway.pinata.cloud",
    ]
    random.shuffle(ipfs_gateways)
    for ipfs_gateway in ipfs_gateways:
        retries = 0
        while retries < MAX_RETRIES:
            final_url = f'https://{ipfs_gateway}/ipfs/{ipfs_cid}'
            LOGGER.info('Downloading from: ' + final_url)
            try:
                response = requests.get(final_url)
                if response.status_code == 200:
                    return response
            except:
                pass

            retries += 1
    return None
