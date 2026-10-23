"""Regression test: full-length (128-byte) NFT commitments must be storable.

Real failure this guards against:
tx fd548bbc570429d6868ab057d7fe19b4a6d2ef0337f849671b4b5220aa57a69f
block 951147 vout 0/1 carry 128-byte commitments (256 hex chars) and raised
psycopg2.errors.StringDataRightTruncation on the old varchar(255) column,
which made the scanner drop the transaction.
"""
import pytest

from bcmr_main.models import Token
from bcmr_main.utils import save_token

MAX_COMMITMENT_BYTES = 128
MAX_COMMITMENT_HEX = MAX_COMMITMENT_BYTES * 2  # 256


@pytest.mark.django_db
class TestNftCommitmentLength:

    def test_column_fits_a_full_length_commitment(self):
        field = Token._meta.get_field('commitment')

        assert field.max_length >= MAX_COMMITMENT_HEX, (
            f'commitment column is {field.max_length} chars but a 128-byte '
            f'commitment hex-encodes to {MAX_COMMITMENT_HEX}'
        )

    def test_save_token_with_max_length_commitment(self):
        commitment = 'ab' * MAX_COMMITMENT_BYTES
        assert len(commitment) == MAX_COMMITMENT_HEX

        save_token(
            'fd548bbc570429d6868ab057d7fe19b4a6d2ef0337f849671b4b5220aa57a69f',
            '247820df401bfc8f11e13170812fc99cb986f84d5d5f4a5cd42d9645a876ce6f',
            0,
            commitment=commitment,
            capability=Token.Capability.MUTABLE,
            is_nft=True,
        )

        token = Token.objects.get(commitment=commitment)
        assert token.commitment == commitment
        assert token.is_nft is True

    def test_save_token_with_empty_commitment(self):
        # Empty commitments are valid (immutable NFTs with no data).
        save_token('txid-empty', 'cat-empty', 0, commitment='', capability='none',
                   is_nft=True)

        assert Token.objects.get(category='cat-empty').commitment == ''
