from bcmr_main.models import IdentityOutput
from bcmr_main.bchn import BCHN


def traverse_authchain(txid, ancestor_tx, block_txns, outputs_ids=[]):
    """
    Traverse the authchain in the transactions in this block
    """
    print('--- TRAVERSE:', txid)
    tx_obj, _ = IdentityOutput.objects.get_or_create(txid=txid)
    ancestor_obj, _ = IdentityOutput.objects.get_or_create(txid=ancestor_tx)
    ancestor_obj.spent = True
    ancestor_obj.spender = tx_obj
    ancestor_obj.save()

    outputs_ids += [tx_obj.id, ancestor_obj.id]

    if not ancestor_obj.authbase:
        bchn = BCHN()
        tx = bchn.get_transaction(ancestor_tx)

        input_txids = []
        for tx_input in tx['inputs']:
            if tx_input['spent_index'] == 0:
                input_txids.append(tx_input['txid'])

        ancestor_txns = set(input_txids).intersection(set(block_txns))
        if ancestor_txns:
            for ancestor_txn in ancestor_txns:
                return traverse_authchain(ancestor_tx, ancestor_txn, block_txns, outputs_ids)
    
    return outputs_ids
