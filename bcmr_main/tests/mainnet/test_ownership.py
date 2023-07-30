import pytest

from bcmr_main.tasks import process_tx
from bcmr_main.models import Ownership, Token
from bcmr_main.bchn import BCHN


bchn = BCHN()


@pytest.mark.django_db
class TestOwnership:

    def test_ownership_tracking(self):
        # Check if identity output is not saved
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 0

        # Use the Emerald DAO as test where one minting NFT token was created
        genesis_txid = '00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6'
        genesis_tx = bchn._get_raw_transaction(genesis_txid)
        process_tx(genesis_tx)

        # Check if the token record was saved
        tokens = Token.objects.all()
        assert tokens.count() == 1

        # Check if the ownership record was saved
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 1

        # Process the first minting tx of Emerald DAO
        minting_txid = 'f258e5daadc823cd5fc99c1d02ee4c822185a27afd300f7a69a2c33ef893c29e' 
        minting_tx = bchn._get_raw_transaction(minting_txid)
        process_tx(minting_tx)

        # Check if the token records were saved
        # This tx has created 3 new tokens
        tokens = Token.objects.all()
        assert tokens.count() == 4

        # Check if the ownership records were saved
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 4

        # Process a transfer of NFT
        transfer_txid = '3e3a86980104c2a575ad8ef69963021e25db2134870de63a643292d8cc35e820'
        transfer_tx = bchn._get_raw_transaction(transfer_txid)
        process_tx(transfer_tx)

        # Check token records to make sure no new tokens were created
        tokens = Token.objects.all()
        assert tokens.count() == 4

        # Check if ownership records, 1 record must be created
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 5

        # Check that one ownership record is a transfer
        ownership_transfer_check = Ownership.objects.filter(acquired_via='transfer')
        assert ownership_transfer_check.count() == 1
        token_transferred = ownership_transfer_check.last()
        assert token_transferred.token.commitment == '010005269a0000000000'

        # ownerships = Ownership.objects.all()
        # for ownership in ownerships:
        #     print('#######################')
        #     print(ownership.id, ownership.token)
        #     print(ownership.txid, ownership.acquired_via)
        #     print(ownership.date_acquired)
        
        # assert 1 == 2


        # # Process a downstream tx -- i.e. minting of 300th NFT
        # minting_txid = '3dc13a782765207b7db9b425adb9d5708f83f6f919f89e3f22c06373bcef2b10'
        # minting_tx = bchn._get_raw_transaction(minting_txid)
        # process_tx(minting_tx)

        # # Check if the token records were saved
        # # This tx has created 2 new tokens
        # tokens = Token.objects.all()
        # assert tokens.count() == 6
