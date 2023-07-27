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

        # Use the Emerald DAO as test where the token genesis did not immediately contain the BCMR update
        genesis_txid = '00003c40fa202816c357350eaa2e7ec2b47766209604941789ecf814f98ba4a6'
        genesis_tx = bchn._get_raw_transaction(genesis_txid)
        process_tx(genesis_tx)

        # Check if the token record was saved
        tokens = Token.objects.all()
        assert tokens.count() == 1

        # Check if the ownership record was saved
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 1

        transfer_txid = '3dc13a782765207b7db9b425adb9d5708f83f6f919f89e3f22c06373bcef2b10'
        transfer_tx = bchn._get_raw_transaction(transfer_txid)
        process_tx(transfer_tx)

        # Check if the ownership record was saved
        ownerships = Ownership.objects.all()
        assert ownerships.count() == 2
