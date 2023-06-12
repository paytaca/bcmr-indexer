import pytest
import json
import os
from unittest.mock import patch
from bcmr_main.tasks import process_tx
from bcmr_main.models import IdentityOutput, Token, Registry


@pytest.mark.django_db
class TestIdentityOutputs:

    def test_saving_authbase_and_genesis(self):
        # Check if identity output table is empty
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # process a non-authbase tx
        authbase_tx = '07275f68d14780c737279898e730cec3a7b189a761caf43b4197b60a7c891a97'
        process_tx(authbase_tx)

        # Check if identity output is not saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # process a genesis tx
        genesis_tx = 'd5721db8841ecb61ec73daeb2df7df88b180d5029061d4845efc7cb29c42183b'
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
        authbase_tx_obj = IdentityOutput.objects.get(txid=authbase_tx)
        assert authbase_tx_obj.txid == authbase_tx
        assert authbase_tx_obj.authbase == True
        assert authbase_tx_obj.genesis == False

        # check if genesis is properly saved
        genesis_tx_obj = IdentityOutput.objects.get(txid=genesis_tx)
        assert genesis_tx_obj.txid == genesis_tx
        assert genesis_tx_obj.authbase == False
        assert genesis_tx_obj.genesis == True
        
        # check if identity output for authbase is properly marked as
        # spent by genesis tx and in the right order
        assert authbase_tx_obj.spent == True
        assert authbase_tx_obj.spender.txid == genesis_tx
        assert authbase_tx_obj.id == (genesis_tx_obj.id - 1)


    def test_authchain_traversal(self):
        # Check if identity output is not saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 0

        # Use the Emerald DAO as test where the token genesis did not immediately contain the BCMR update
        genesis_tx = '00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6'
        process_tx(genesis_tx)

        # Check if the token record was saved
        tokens = Token.objects.all()
        assert tokens.count() == 1

        # First BCMR update
        bcmr_update_tx = '963af3f74933e5f5b204671b25a8f467f640bc56e8d3f9104a1ec8e118d7c919'
        process_tx(bcmr_update_tx)

        # Check if identity outputs are saved
        identity_outputs = IdentityOutput.objects.all()
        assert identity_outputs.count() == 3

        registries = Registry.objects.all()
        assert registries.count() == 1

        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 0

        # Second BCMR update
        bcmr_update_tx = 'c8d08e34f74a83c470ff35d0bfebab81c5ade5e10df661a555f19b6ee05df01c'
        process_tx(bcmr_update_tx)

        registries = Registry.objects.filter(valid=True)
        assert registries.count() == 0

        # Third BCMR update
        bcmr_update_tx = '66976cd8b18b4faafd7ad7b93540c65257179ed14218decb90c8613cddaf78c1'
        process_tx(bcmr_update_tx)

        registries = Registry.objects.filter(valid=True)
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
