import pytest

from bcmr_main.models import Ownership, Token
from bcmr_main.tasks import process_tx


@pytest.mark.django_db
class TestOwnership:

    def test_saving_ownership(self):
        genesis_tx = '6ee7977ddf9ede8a4d24cd1a81bbaf18f83af9814d46ad291c06a37ceb82c6bc'
        minting_nft_owner = 'bchtest:qrw44adl0lxjwndduq6ntpv3l6nd7n0c4vgjlyezqr'
        token_id = 'd3c03c036141b86815167a12bed6d14376d40e2572b7dff1d45a54ce274646b3'

        process_tx(genesis_tx)
        
        tokens = Token.objects.all()
        assert tokens.count() == 1
        
        token = Token.objects.filter(
            category=token_id,
            capability=Token.Capability.MINTING,
            commitment=''
        )
        assert token.exists()

        if token.exists():
            token = token.first()

            ownerships = Ownership.objects.all()
            assert ownerships.count() == 1

            ownership = Ownership.objects.filter(
                txid=genesis_tx,
                token=token,
                index=1
            )
            assert ownership.exists()

            if ownership.exists():
                ownership = ownership.first()
                assert ownership.address == minting_nft_owner
                assert ownership.token.category == token_id
        
        # multiple token children of same comitment and capability
        txid = '42e852818027a7a469aef69d3d2d9bf797d8018e2f67737e12655ec59539b852'
        process_tx(txid)

        # minting and mutables of same token data
        tokens = Token.objects.all()
        assert tokens.count() == 2

        ownerships = Ownership.objects.all()
        assert ownerships.count() == 1402


    def test_spending_ownership(self):
        txid = '528f240b27e1e17a221bb9c1de3e81ad756495a653e8cf2d45ac0b9eb36a302e'
        process_tx(txid)

        ownerships = Ownership.objects.all()
        assert ownerships.count() == 5

        tokens = Token.objects.all()
        assert tokens.count() == 4


    # TODO: find a transaction containing a burn
    def test_burning_ownership(self):
        pass
