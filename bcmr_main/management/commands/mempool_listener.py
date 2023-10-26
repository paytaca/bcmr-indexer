#!/usr/bin/env python2
# Copyright (c) 2014-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from django.core.management.base import BaseCommand

from bcmr_main.bchn import *
from bcmr_main.op_return import process_op_return
from bcmr_main.tasks import process_tx

import logging
import binascii
import zmq
from bitcoinrpc.authproxy import AuthServiceProxy


LOGGER = logging.getLogger(__name__)


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
                    decoded = self.rpc_connection.decoderawtransaction(body.hex())
                    outputs = decoded.get('vout')
                    for output in outputs:
                        if output['type'] == 'nulldata' and output['scriptPubKey'].get('asm').startswith('OP_RETURN'):
                            index = output['n']
                            txid  = decoded['txid']
                            asm   = output['scriptPubKey'].get('asm')
                            process_op_return(
                                txid,
                                index,
                                asm,
                                #publisher?,
                                #time?
                            )
                            # asm_arr = output['scriptPubKey'].get('asm').split(' ') 
                            # if len(asm_arr) >= 4:  
                            #     uris_hex = output['scriptPubKey'].get('asm').split(' ')[4]
                            #     uris = bytes.fromhex(uris_hex).decode('utf-8')
                            #     uris = uris.split(';')
                            #     if len(uris)
        except KeyboardInterrupt:
            self.zmqContext.destroy()

z = ZMQHandler()
z.start()
