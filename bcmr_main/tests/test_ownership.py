import pytest

from bcmr_main.models import Ownership, Token
from bcmr_main.tasks import process_tx

# NOTE: all TXIDs used here are chipnet transactions

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


    def test_token_spending(self):
        parent_tx = 'f4d4cabb9aa5669f041efc216f3bfb0f1b72e72cb97a5e147273b0cef3f91c4c'
        process_tx(parent_tx)

        ownerships = Ownership.objects.all()
        spent_ownerships = Ownership.objects.filter(spent=True)
        tokens = Token.objects.all()

        assert ownerships.count() == 5
        assert spent_ownerships.count() == 0
        assert tokens.count() == 4

        child_tx = '528f240b27e1e17a221bb9c1de3e81ad756495a653e8cf2d45ac0b9eb36a302e'
        process_tx(child_tx)

        ownerships = Ownership.objects.all()
        spent_ownerships = Ownership.objects.filter(spent=True, spender=child_tx)
        tokens = Token.objects.all()

        assert ownerships.count() == 10
        assert spent_ownerships.count() == 4
        assert tokens.count() == 4

    
    def test_token_mutation(self):
        # sequential relative txn processing
        relative_txns = [
            '7cd0d477d194fb3b67b50507b749b5eda1103d71dd1aebc23d71880c3d440892',
            '64781913f7f227044e7f43c0172ae5cda0cddde0187bc6bed629e433e9f30455',
            'd9e2a25c0e92c122bb1028fa2e41281d6027796d315bedb629210206a0428c9b'
        ]
        expected_token_count_addition = 2
        expected_token_count = 2
        expected_ownership_count_addition = 2
        expected_ownership_count = 2

        for txid in relative_txns:
            process_tx(txid)

            ownerships = Ownership.objects.all()
            burned_ownerships = ownerships.filter(burned=True)
            tokens = Token.objects.all()

            assert ownerships.count() == expected_ownership_count
            assert burned_ownerships.count() == 0
            assert tokens.count() == expected_token_count

            expected_ownership_count += expected_ownership_count_addition
            expected_token_count += expected_token_count_addition

        first_ownership = Ownership.objects.get(txid=relative_txns[0], index=0)
        second_ownership = Ownership.objects.get(txid=relative_txns[1], index=0)
        third_ownership = Ownership.objects.get(txid=relative_txns[2], index=0)

        assert third_ownership.spender is None
        assert third_ownership.spent == False

        assert second_ownership.spender == third_ownership.txid
        assert second_ownership.spent == True

        assert first_ownership.spender == second_ownership.txid
        assert first_ownership.spent == True
        

        # reset model records for the unordered txid testing below
        Ownership.objects.all().delete()
        Token.objects.all().delete()

        # same block relative txn processing
        relative_txns = [
            '64781913f7f227044e7f43c0172ae5cda0cddde0187bc6bed629e433e9f30455',
            '7cd0d477d194fb3b67b50507b749b5eda1103d71dd1aebc23d71880c3d440892',
            'd9e2a25c0e92c122bb1028fa2e41281d6027796d315bedb629210206a0428c9b'
        ]
        expected_token_count_addition = 2
        expected_token_count = 2
        expected_ownership_count_addition = 2
        expected_ownership_count = 2

        for txid in relative_txns:
            process_tx(txid)

            ownerships = Ownership.objects.all()
            burned_ownerships = ownerships.filter(burned=True)
            tokens = Token.objects.all()

            assert ownerships.count() == expected_ownership_count
            assert burned_ownerships.count() == 0
            assert tokens.count() == expected_token_count

            expected_ownership_count += expected_ownership_count_addition
            expected_token_count += expected_token_count_addition
        

        second_ownership = Ownership.objects.get(txid=relative_txns[0], index=0)
        first_ownership = Ownership.objects.get(txid=relative_txns[1], index=0)
        third_ownership = Ownership.objects.get(txid=relative_txns[2], index=0)

        assert third_ownership.spender is None
        assert third_ownership.spent == False

        assert second_ownership.spender == third_ownership.txid
        assert second_ownership.spent == True

        assert first_ownership.spender == second_ownership.txid
        assert first_ownership.spent == True


    # TODO: find a transaction containing a burn
    def test_token_burning(self):
        pass
