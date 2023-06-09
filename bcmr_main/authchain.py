from bcmr_main.models import IdentityOutput
from bcmr_main.bchn import BCHN


def traverse_authchain(spent_txid):
    bchn = BCHN()
    tx = bchn._get_raw_transaction(spent_txid)
    
    inputs = tx['vin']
    outputs = tx['vout']
    identity_input = inputs[0]

    if 'coinbase' in identity_input.keys():
        return

    identity_input_txid = identity_input['txid']
    identity_input_index = identity_input['vout']
    token_outputs = []

    for output in outputs:
        scriptPubKey = output['scriptPubKey']
        output_type = scriptPubKey['type']
        if output_type in ['pubkeyhash', 'scripthash']:
            if 'tokenData' in output.keys():
                token_outputs.append(output)

    # stop recursion when we reach genesis transaction
    if token_outputs:
        main_token_output = token_outputs[0]
        main_token_data = main_token_output['tokenData']
        category = main_token_data['category']

        if category == identity_input_txid:
            return main_token_data

    return traverse_authchain(identity_input_txid)
