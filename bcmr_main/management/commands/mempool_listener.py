#!/usr/bin/env python2
# Copyright (c) 2014-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
import requests
import threading
from jsonschema import ValidationError
from django.core.management.base import BaseCommand

from bcmr_main.bchn import *
from bcmr_main.ipfs import download_ipfs_bcmr_data
from bcmr_main.models import Registry
from bcmr_main.app.BitcoinCashMetadataRegistry import BitcoinCashMetadataRegistry

import logging
from bcmr_main.utils import encode_str
from bcmr_main.tasks import process_op_return_from_mempool
import zmq
from bitcoinrpc.authproxy import AuthServiceProxy

LOGGER = logging.getLogger(__name__)

def load_registry(txid, op_return_output):
    compute_hash = encode_str
    if Registry.objects.filter(txid=txid).exists():
        return
    if op_return_output['scriptPubKey']['type'] == 'nulldata' and op_return_output['scriptPubKey']['asm'].startswith('OP_RETURN'):
        asm_arr = op_return_output['scriptPubKey'].get('asm').split(' ') 
        if len(asm_arr) >= 4:  
            published_content_hash_hex = asm_arr[2]
            published_uris_hex = asm_arr[3]
            published_uris_string = bytes.fromhex(published_uris_hex).decode('utf-8')
            published_uris_string = published_uris_string.split(';')
            registry_contents = None
            published_uri = None
            response = None
            for uri in published_uris_string:
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
                published_content_hash = bytes.fromhex(published_content_hash_hex).decode() 
                dns_resolved_content_hash = compute_hash(registry_contents)
                validity_checks = {
                    'bcmr_file_accessible': True,
                    'bcmr_hash_match': published_content_hash == dns_resolved_content_hash,
                    'identities_match': None
                }
                try:
                    BitcoinCashMetadataRegistry.validate_contents(registry_contents)
                except ValidationError: 
                    pass 
                try:
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
           
class ZMQHandler():

    def __init__(self):
        self.url = "tcp://zmq:28332"
        self.BCHN = BCHN()

        self.zmqContext = zmq.Context()
        self.zmqSubSocket = self.zmqContext.socket(zmq.SUB)
        self.zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "rawtx")
        self.zmqSubSocket.connect(self.url)
        self.rpc_connection = AuthServiceProxy(settings.BCHN_NODE)

    def start(self):
        try:
            while True:
                msg = self.zmqSubSocket.recv_multipart()
                topic = msg[0].decode()
                body = msg[1]
                if topic == "rawtx":
                    try:
                        process_op_return_from_mempool.delay(body.hex())
                        # decoded = self.rpc_connection.decoderawtransaction(body.hex())
                        # outputs = decoded.get('vout')
                        # for output in outputs:
                        #     if output['scriptPubKey']['type'] == 'nulldata' and output['scriptPubKey']['asm'].startswith('OP_RETURN'):
                        #         t = threading.Thread(target=load_registry, args=(decoded['txid'],output))
                        #         t.start()
                    except Exception as e:
                        LOGGER.info(msg='Error processing op_return from mempool')
                
        except KeyboardInterrupt:
            self.zmqContext.destroy()
        except Exception as e:
            LOGGER.info(msg=e)

class Command(BaseCommand):
    help = "Start mempool tracker using ZMQ"

    def handle(self, *args, **options):
        daemon = ZMQHandler()
        daemon.start()

