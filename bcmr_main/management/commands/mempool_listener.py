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
import time
import zmq

LOGGER = logging.getLogger(__name__)

# Delay between reconnect attempts when the ZMQ socket dies.
RECONNECT_DELAY = 5


class ZMQHandler():

    def __init__(self):
        self.url = f"tcp://{settings.BCHN_HOST}:{settings.BCHN_ZMQ_PORT}"
        self.zmqContext = zmq.Context()
        self.zmqSubSocket = None

    def connect(self):
        if self.zmqSubSocket is not None:
            try:
                self.zmqSubSocket.close(linger=0)
            except Exception:
                pass

        self.zmqSubSocket = self.zmqContext.socket(zmq.SUB)
        self.zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "rawtx")
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_CNT, 10)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
        self.zmqSubSocket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 1)
        self.zmqSubSocket.connect(self.url)

    def start(self):
        node = BCHN()
        self.connect()

        while True:
            try:
                msg = self.zmqSubSocket.recv_multipart()
            except KeyboardInterrupt:
                self.zmqContext.destroy()
                return
            except zmq.ZMQError:
                # Socket died (node restart / tunnel drop). Reconnect instead
                # of crashing the listener and losing mempool coverage.
                LOGGER.exception(
                    'ZMQ socket error, reconnecting in %ss.', RECONNECT_DELAY
                )
                time.sleep(RECONNECT_DELAY)
                try:
                    self.connect()
                except Exception:
                    LOGGER.exception('ZMQ reconnect failed')
                continue

            try:
                topic = msg[0].decode()
                body = msg[1]
                if topic != "rawtx":
                    continue

                tx_hex = body.hex()
                txid = transaction.calc_txid(tx_hex)
                LOGGER.info(f'Received mempool tx: {txid}')
                tx = node.decode_raw_transaction(tx_hex)
                if not tx:
                    LOGGER.warning(f'Could not decode mempool tx: {txid}')
                    continue

                # Process inline (the decoded tx carries Decimal values that
                # Celery's JSON serializer cannot encode). Isolate failures so
                # one bad transaction does not kill the listener.
                try:
                    process_tx(tx)
                except Exception:
                    LOGGER.exception(f'Failed to process mempool tx: {txid}')
            except Exception:
                LOGGER.exception('Failed to handle mempool message')


class Command(BaseCommand):
    help = "Start mempool tracker using ZMQ"

    def handle(self, *args, **options):
        daemon = ZMQHandler()
        daemon.start()
