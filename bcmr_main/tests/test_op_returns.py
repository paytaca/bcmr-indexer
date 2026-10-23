from unittest import mock

import pytest
from bcmr_main import op_return
from bcmr_main.op_return import process_op_return
from bcmr_main.utils import timestamp_to_date
from bcmr_main.models import Registry


VALID_OP_RETURNS = [
    # BitCats BCMR
    (
        '3ed294f4894f159125a87a6e6681f0dd71d3b2f51c275a15b502138aba3399c8',
        'OP_RETURN 1380795202 65353166303362396131373738636536373032616365323437393230313231646361303730653365356166643066333062356530383961306363376330303635 697066732e7061742e6d6e2f697066732f516d5155765a675763737231535755426f7a78537066704257646f4a376259764474566e35556233705447784455',
        1685966924,
        'https://ipfs.pat.mn/ipfs/QmQUvZgWcsr1SWUBozxSpfpBWdoJ7bYvDtVn5Ub3pTGxDU'
    ),
    # Fallout token BCMR
    (
        '2edbe1d87de2a93f26cf4764342f67b0fdba51f05ae3cc067c1ac3746454afcb',
        'OP_RETURN 1380795202 a8dd9f3f77efec7d4c159cbd28f6181e704dd0c298baea0cc3488cd1a176dc91 63332d736f66742e636f6d2f746f6b656e732f66616c6c6f75745f636f696e2e6a736f6e',
        1684157526,
        'https://c3-soft.com/tokens/fallout_coin.json'
    )
]


@pytest.mark.django_db
class TestOpReturnValidation:

    @pytest.mark.parametrize("txid, op_return, date, bcmr_url", VALID_OP_RETURNS)
    def test_op_return_validation(self, txid, op_return, date, bcmr_url):
        date = timestamp_to_date(date)

        # Check if registry table is empty
        registries = Registry.objects.all()
        assert registries.count() == 0

        # Check if the BCMR is found valid
        validity_checks, decoded_bcmr_url = process_op_return(
            txid,
            0,
            op_return,
            None,
            date
        )
        assert validity_checks['bcmr_hash_match'], decoded_bcmr_url == bcmr_url

        # Check if the record for this BCMR is saved in the registry table
        registries = Registry.objects.all()
        assert registries.count() == 1

        registry = registries.first()
        assert registry.txid == txid
        assert registry.op_return == op_return
        assert registry.bcmr_url == bcmr_url


@pytest.mark.django_db
class TestWatchedRegistryIdempotency:
    """`watch_registry_changes` re-runs every 20s, so an unchanged registry must
    not be written again: each save fires post_save signals that invalidate
    caches and rewrite the row, forever."""

    TXID, OP_RETURN, DATE, _URL = VALID_OP_RETURNS[0]

    def _seed(self):
        return process_op_return(
            self.TXID, 0, self.OP_RETURN, None, timestamp_to_date(self.DATE)
        )

    def test_second_pass_does_not_write_an_unchanged_registry(self):
        self._seed()
        registry = Registry.objects.get()
        original_save = Registry.save
        saved = []

        def counting_save(instance, *args, **kwargs):
            saved.append(instance.pk)
            return original_save(instance, *args, **kwargs)

        with mock.patch.object(Registry, 'save', counting_save):
            validity_checks, url = process_op_return(
                self.TXID, 0, self.OP_RETURN, None, timestamp_to_date(self.DATE)
            )

        assert validity_checks['bcmr_hash_match'] is True
        assert saved == [], "unchanged registry was written %s time(s)" % len(saved)
        assert Registry.objects.get().contents == registry.contents

    def test_changed_contents_are_still_saved(self):
        self._seed()
        before = Registry.objects.get().contents

        class FakeResponse:
            status_code = 200
            text = '{"registry_version": 2, "name": "changed"}'

        with mock.patch.object(op_return, 'download_url', return_value=FakeResponse()), \
             mock.patch.object(op_return, 'encode_str', return_value=None), \
             mock.patch.object(
                 op_return.BitcoinCashMetadataRegistry, 'validate_contents'
             ):
            process_op_return(
                self.TXID, 0, self.OP_RETURN, None, timestamp_to_date(self.DATE)
            )

        after = Registry.objects.get().contents
        assert after != before
        assert after == {'registry_version': 2, 'name': 'changed'}
