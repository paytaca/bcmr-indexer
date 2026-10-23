from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

from django.conf import settings
from django.utils import timezone

import logging
import time


LOGGER = logging.getLogger(__name__)


class BCHN(object):

    def __init__(self, timeout=None):
        self.max_retries = getattr(settings, 'BCHN_RPC_MAX_RETRIES', 3)
        self.rpc_timeout = timeout or getattr(settings, 'BCHN_RPC_TIMEOUT', 60)
        self._block_heights = {}
        self._block_heights_limit = 256

        self.rpc_connection = self._connect()

    def _connect(self):
        # AuthServiceProxy builds its socket without a timeout unless one is
        # passed. Without it, an RPC call over a half-open connection (dropped
        # SSH tunnel, NAT timeout, node restart) blocks forever and the caller
        # never logs anything again.
        try:
            proxy = AuthServiceProxy(
                settings.BCHN_NODE, timeout=self.rpc_timeout
            )
        except TypeError:
            # Older python-bitcoinrpc builds do not accept a timeout kwarg.
            proxy = AuthServiceProxy(settings.BCHN_NODE)

        conn = getattr(proxy, '_AuthServiceProxy__conn', None)
        if conn is not None:
            conn.timeout = self.rpc_timeout
            if conn.sock is not None:
                conn.sock.settimeout(self.rpc_timeout)

        return proxy

    def _reset_connection(self):
        # A failed request can leave the underlying httplib connection in a
        # broken state; retrying on the same proxy would keep failing.
        try:
            self.rpc_connection = self._connect()
        except Exception:
            LOGGER.exception('Unable to recreate BCHN RPC connection')

    def _call(self, method, *args):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return getattr(self.rpc_connection, method)(*args)
            except JSONRPCException as exc:
                # The node answered: this is a deterministic error (unknown
                # txid, block not found, bad params). Retrying the same request
                # would just burn ~3.5s per call and still fail.
                LOGGER.warning('BCHN RPC %s rejected: %s', method, exc)
                raise
            except Exception as exc:
                last_exception = exc
                LOGGER.warning(
                    'BCHN RPC %s failed (attempt %s/%s): %s',
                    method, attempt, self.max_retries, exc
                )
                self._reset_connection()
                if attempt < self.max_retries:
                    time.sleep(attempt * 1.25)
        raise last_exception

    def get_latest_block(self):
        return self._call('getblockcount')

    def get_block(self, block):
        try:
            block_hash = self._call('getblockhash', block)
            block_data = self._call('getblock', block_hash, 3)
            return block_data['tx']
        except Exception:
            # Caller is expected to retry this block on the next poll instead
            # of dying (which used to crash the whole scanner process).
            LOGGER.exception('Failed to fetch block #%s', block)
            return None

    def get_block_height(self, block_hash):
        if block_hash in self._block_heights:
            return self._block_heights[block_hash]

        try:
            block = self._call('getblock', block_hash)
            height = block['height']
        except Exception:
            LOGGER.exception('Failed to resolve height of block %s', block_hash)
            return None

        # Every tx in a block shares the same blockhash; caching this turns one
        # RPC call per transaction into one call per block.
        if len(self._block_heights) >= self._block_heights_limit:
            self._block_heights.clear()
        self._block_heights[block_hash] = height
        return height

    def _get_raw_transaction(self, txid):
        return self._call('getrawtransaction', txid, 2)

    def get_transaction(self, tx_hash):
        try:
            txn = self._get_raw_transaction(tx_hash)
            if txn:
                return self._parse_transaction(txn)
        except Exception:
            LOGGER.exception('Failed to fetch transaction %s', tx_hash)

    def _parse_transaction(self, txn, include_outputs=True):
        tx_hash = txn['hash']
        
        # NOTE: very new transactions doesnt have timestamp
        time = timezone.now().timestamp()
        if 'time' in txn.keys():
            time = txn['time']

        transaction = {
            'txid': tx_hash,
            'timestamp': time,
            'valid': True
        }
        transaction['inputs'] = []

        for tx_input in txn['vin']:
            input_txid = tx_input['txid']

            if 'prevout' in tx_input.keys():
                prevout = tx_input['prevout']
                value = prevout['value']
                input_token_data = None
                scriptPubKey = prevout['scriptPubKey']

                if 'address' in scriptPubKey.keys():
                    input_address = scriptPubKey['address']
                else:
                    # for multisig input prevouts (no address given on data)
                    input_address = self.get_input_address(input_txid, tx_input['vout'])

                if 'tokenData' in prevout.keys():
                    input_token_data = prevout['tokenData']
            else:

                # value = int(float(tx_input['value'] * (10 ** 8)))
                value = tx_input.get('value')
                if value: 
                    value = int(float(value * (10 ** 8)))
                input_token_data = self.get_input_token_data(input_txid, tx_input['vout'])
                input_address = self.get_input_address(input_txid, tx_input['vout'])

            data = {
                'txid': input_txid,
                'spent_index': tx_input['vout'],
                'value': value,
                'token_data': input_token_data,
                'address': input_address
            }
            transaction['inputs'].append(data)

        if include_outputs:
            transaction['outputs'] = []
            outputs = txn['vout']

            for tx_output in outputs:
                if 'value' in tx_output.keys() and 'addresses' in tx_output['scriptPubKey'].keys():
                    # sats_value = int(float(tx_output['value'] * (10 ** 8)))
                    sats_value = tx_output.get('value')
                    if sats_value:
                        sats_value = int(float(sats_value * (10 ** 8)))
                    data = {
                        'address': tx_output['scriptPubKey']['addresses'][0],
                        'value': sats_value,
                        'index': tx_output['n'],
                        'token_data': None
                    }
                    if 'tokenData' in tx_output.keys():
                        data['token_data'] = tx_output['tokenData']
                    transaction['outputs'].append(data)

        # transaction['tx_fee'] = txn['fee'] * (10 ** 8)
        transaction['tx_fee'] = txn.get('fee')
        if transaction['tx_fee']:
            transaction['tx_fee'] = transaction['tx_fee'] * (10 ** 8)
        return transaction
    
    def get_input_address(self, txid, vout_index):
        previous_tx = self._get_raw_transaction(txid)
        previous_out = previous_tx['vout'][vout_index]
        if 'addresses' in previous_out['scriptPubKey'].keys():
            return previous_out['scriptPubKey']['addresses'][0]

    def get_input_token_data(self, txid, vout_index):
        previous_tx = self._get_raw_transaction(txid)
        previous_out = previous_tx['vout'][vout_index]

        if 'tokenData' in previous_out.keys():
            return previous_out['tokenData']
        return None

    def decode_raw_transaction(self, tx_hex):
        return self._call('decoderawtransaction', tx_hex)
