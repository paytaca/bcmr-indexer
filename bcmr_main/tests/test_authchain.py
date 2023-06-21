import pytest
import json
import os
from unittest.mock import patch

from bcmr_main.tasks import process_tx
from bcmr_main.models import IdentityOutput, Token, Registry
from bcmr_main.bchn import BCHN
from bcmr_main.tasks import resolve_metadata


bchn = BCHN()


@pytest.mark.django_db
class TestIdentityOutputs:

    def test_saving_authbase_and_genesis(self):
        # Check if identity output table is empty
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # process a non-authbase tx
        authbase_txid = '07275f68d14780c737279898e730cec3a7b189a761caf43b4197b60a7c891a97'
        authbase_tx = bchn._get_raw_transaction(authbase_txid)
        process_tx(authbase_tx)

        # Check if identity output is not saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # process a genesis tx
        genesis_txid = 'd5721db8841ecb61ec73daeb2df7df88b180d5029061d4845efc7cb29c42183b'
        genesis_tx = bchn._get_raw_transaction(genesis_txid)
        process_tx(genesis_tx)

        # Check if identity output is saved
        identity_outputs = IdentityOutput.objects.all()
        for identity_output in identity_outputs:
            spender = None
            if identity_output.spender:
                spender = identity_output.spender.txid
            
            # prints when test fails
            print(
                identity_output.id,
                identity_output.txid,
                identity_output.authbase,
                identity_output.genesis,
                identity_output.spent,
                spender
            )

        # check that 2 identity outputs were created -- one for the genesis and one for authbase
        assert identity_outputs.count() == 2

        # check if authbase is properly saved
        authbase_tx_obj = IdentityOutput.objects.get(txid=authbase_txid)
        assert authbase_tx_obj.txid == authbase_txid
        assert authbase_tx_obj.authbase == True
        assert authbase_tx_obj.genesis == False

        # check if genesis is properly saved
        genesis_tx_obj = IdentityOutput.objects.get(txid=genesis_txid)
        assert genesis_tx_obj.txid == genesis_txid
        assert genesis_tx_obj.authbase == False
        assert genesis_tx_obj.genesis == True
        
        # check if identity output for authbase is properly marked as
        # spent by genesis tx and in the right order
        assert authbase_tx_obj.spent == True
        assert authbase_tx_obj.spender.txid == genesis_txid
        assert authbase_tx_obj.id == (genesis_tx_obj.id - 1)


    def test_saving_ancestor_txns(self):
        # Check if identity output is not saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # Use the Emerald DAO as test where the token genesis did not immediately contain the BCMR update
        genesis_txid = '00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6'
        genesis_tx = bchn._get_raw_transaction(genesis_txid)
        process_tx(genesis_tx)

        # Check if the token record was saved
        tokens = Token.objects.all()
        assert tokens.count() == 1

        # First BCMR update
        bcmr_update_txid = '963af3f74933e5f5b204671b25a8f467f640bc56e8d3f9104a1ec8e118d7c919'
        bcmr_update_tx = bchn._get_raw_transaction(bcmr_update_txid)
        process_tx(bcmr_update_tx)

        # Check if identity outputs are saved
        identity_outputs = IdentityOutput.objects.all()
        for io in identity_outputs:
            print(
                'SAVED IDENTITY OUTPUTS:',
                io.txid,
                io.authbase,
                io.genesis
            )
        assert identity_outputs.count() == 3

        registries = Registry.objects.all()
        assert registries.count() == 1

        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 0

        # Second BCMR update
        bcmr_update_txid = 'c8d08e34f74a83c470ff35d0bfebab81c5ade5e10df661a555f19b6ee05df01c'
        bcmr_update_tx = bchn._get_raw_transaction(bcmr_update_txid)
        process_tx(bcmr_update_tx)

        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 0

        # Third BCMR update
        bcmr_update_txid = '66976cd8b18b4faafd7ad7b93540c65257179ed14218decb90c8613cddaf78c1'
        bcmr_update_tx = bchn._get_raw_transaction(bcmr_update_txid)
        process_tx(bcmr_update_tx)

        registries = Registry.objects.filter(validity_checks__bcmr_hash_match=True)
        assert registries.count() == 1

        identity_outputs = IdentityOutput.objects.all()
        for identity_output in identity_outputs:
            spender = None
            if identity_output.spender:
                spender = identity_output.spender.txid
            
            # prints when test fails
            print(
                identity_output.id,
                identity_output.txid,
                identity_output.authbase,
                identity_output.genesis,
                identity_output.spent,
                spender
            )

        assert identity_outputs.count() == 5

    def test_authchain_traversal_on_current_block(self):
        # Check if identity output is not saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # Use the Emerald DAO as test where the token genesis did not immediately contain the BCMR update
        genesis_txid = '00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6'
        genesis_tx = bchn._get_raw_transaction(genesis_txid)
        process_tx(genesis_tx)

        # Check if the token record was saved
        tokens = Token.objects.all()
        assert tokens.count() == 1

        # Check if identity outputs are saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 2

        # Check that no registry has been saved yet
        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 0

        # Third BCMR update
        bcmr_update_txid = '66976cd8b18b4faafd7ad7b93540c65257179ed14218decb90c8613cddaf78c1'
        bcmr_update_tx = bchn._get_raw_transaction(bcmr_update_txid)
        process_tx(bcmr_update_tx)


        authchain_txs = [
            'c8d08e34f74a83c470ff35d0bfebab81c5ade5e10df661a555f19b6ee05df01c',
            '963af3f74933e5f5b204671b25a8f467f640bc56e8d3f9104a1ec8e118d7c919'
        ]
        for authchain_tx in authchain_txs:
            txn = bchn._get_raw_transaction(authchain_tx)
            process_tx(txn)

        # Check if 5 identity outputs are saved
        identity_outputs = IdentityOutput.objects.all()
        for io in identity_outputs:
            spender = ''
            if io.spender:
                spender = io.spender.txid
            print(
                f'IDENTITY OUTPUT #{io.id}:',
                io.txid,
                io.authbase,
                io.genesis,
                f' SPENDER: {spender}',
                io.identities
            )
        assert identity_outputs.count() == 5

        # Check if spent and spenders are properly populated
        identity_output = IdentityOutput.objects.get(txid='00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6')
        assert identity_output.spent == True
        assert identity_output.spender.txid == '963af3f74933e5f5b204671b25a8f467f640bc56e8d3f9104a1ec8e118d7c919'

        identity_output = IdentityOutput.objects.get(txid='963af3f74933e5f5b204671b25a8f467f640bc56e8d3f9104a1ec8e118d7c919')
        assert identity_output.spent == True
        assert identity_output.spender.txid == 'c8d08e34f74a83c470ff35d0bfebab81c5ade5e10df661a555f19b6ee05df01c'

        identity_output = IdentityOutput.objects.get(txid='c8d08e34f74a83c470ff35d0bfebab81c5ade5e10df661a555f19b6ee05df01c')
        assert identity_output.spent == True
        assert identity_output.spender.txid == '66976cd8b18b4faafd7ad7b93540c65257179ed14218decb90c8613cddaf78c1'

        identity_output = IdentityOutput.objects.get(txid='66976cd8b18b4faafd7ad7b93540c65257179ed14218decb90c8613cddaf78c1')
        assert identity_output.spent == False
        assert identity_output.spender == None

        resolve_metadata()

        # Check that there is 1 valid registry
        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 1
