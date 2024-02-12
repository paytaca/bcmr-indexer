from bitcoinrpc.authproxy import AuthServiceProxy

from django.conf import settings
from django.utils import timezone

import socket
import ssl
import time
import json


class BCHN(object):

    def __init__(self):
        self.max_retries = 3
        self.rpc_connection = AuthServiceProxy(settings.BCHN_NODE)
    
    def get_latest_block(self):
        return self.rpc_connection.getblockcount()

    def get_block(self, block):
        retries = 0
        while retries < self.max_retries:
            try:
                block_hash = self.rpc_connection.getblockhash(block)
                block_data = self.rpc_connection.getblock(block_hash, 3)
                return block_data['tx']
            except:
                retries += 1
                time.sleep(retries * 1.25)

    def get_block_height(self, block_hash):
        retries = 0
        while retries < self.max_retries:
            try:
                block = self.rpc_connection.getblock(block_hash)
                return block['height']
            except:
                retries += 1
                time.sleep(retries * 1.25)

    def _get_raw_transaction(self, txid):
        retries = 0
        exception = None
        while retries < self.max_retries:
            try:
                txn = self.rpc_connection.getrawtransaction(txid, 2)
                return txn
            except Exception as exc:
                retries += 1
                exception = exc
                time.sleep(retries * 1.25)
        if exception:
            raise exception

    def get_transaction(self, tx_hash):
        retries = 0
        while retries < self.max_retries:
            try:
                txn = self._get_raw_transaction(tx_hash)
                if txn:
                    return self._parse_transaction(txn)
                break
            except:
                retries += 1
                time.sleep(retries * 1.25)

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
        return previous_out['scriptPubKey']['addresses'][0]

    def get_input_token_data(self, txid, vout_index):
        previous_tx = self._get_raw_transaction(txid)
        previous_out = previous_tx['vout'][vout_index]

        if 'tokenData' in previous_out.keys():
            return previous_out['tokenData']
        return None

    def decode_raw_transaction(self, tx_hex):
        retries = 0
        while retries < self.max_retries:
            try:
                txn = self.rpc_connection.decoderawtransaction(tx_hex)
                return txn
            except Exception as exception:
                retries += 1
                if retries >= self.max_retries:
                    raise exception
                time.sleep(1)
