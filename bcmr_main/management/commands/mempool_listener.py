#!/usr/bin/env python2
# Copyright (c) 2014-2016 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from django.core.management.base import BaseCommand
from bcmr_main.tasks import process_tx
from bitcash import transaction
from bcmr_main.bchn import BCHN
from django.conf import settings
import logging
import zmq

LOGGER = logging.getLogger(__name__)

class ZMQHandler():

    def __init__(self):
        self.url = f"tcp://{settings.BCHN_HOST}:28332"
        self.zmqContext = zmq.Context()
        self.zmqSubSocket = self.zmqContext.socket(zmq.SUB)
        self.zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "rawtx")
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE,1)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_CNT,10)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_IDLE,1)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_INTVL,1)
        self.zmqSubSocket.connect(self.url)

    def start(self):
        node = BCHN()
        try:
            while True:
                msg = self.zmqSubSocket.recv_multipart()
                topic = msg[0].decode()
                body = msg[1]
                if topic == "rawtx":
                    tx_hex = body.hex()
                    txid = transaction.calc_txid(tx_hex)
                    LOGGER.info(f'Received mempool tx: {txid}')
                    tx = node.decode_raw_transaction(tx_hex)
                    process_tx(tx)
        except KeyboardInterrupt:
            self.zmqContext.destroy()
        except Exception as e:
            LOGGER.info(msg=e)

class Command(BaseCommand):
    help = "Start mempool tracker using ZMQ"

    def handle(self, *args, **options):
        daemon = ZMQHandler()
        daemon.start()
