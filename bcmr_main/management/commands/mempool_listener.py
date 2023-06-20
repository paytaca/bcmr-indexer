#!/usr/bin/env python2
# Copyright (c) 2014-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from django.core.management.base import BaseCommand

from bcmr_main.bchn import *
from bcmr_main.tasks import process_tx

import logging
import binascii
import zmq


LOGGER = logging.getLogger(__name__)


class ZMQHandler():

    def __init__(self):
        self.url = "tcp://zmq:28332"
        self.BCHN = BCHN()

        self.zmqContext = zmq.Context()
        self.zmqSubSocket = self.zmqContext.socket(zmq.SUB)
        self.zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "hashtx")
        self.zmqSubSocket.connect(self.url)

    def start(self):
        try:
            while True:
                msg = self.zmqSubSocket.recv_multipart()
                topic = msg[0].decode()
                body = msg[1]

                if topic == "hashtx":
                    tx_hash = binascii.hexlify(body).decode()
                    tx = self.BCHN._get_raw_transaction(tx_hash)
                    inputs = tx['vin']

                    if 'coinbase' in inputs[0].keys():
                        continue
                    
                    process_tx.delay(tx_hash, source='mempool')
        except KeyboardInterrupt:
            zmqContext.destroy()


class Command(BaseCommand):
    help = "Start mempool tracker using ZMQ"

    def handle(self, *args, **options):
        daemon = ZMQHandler()
        daemon.start()
