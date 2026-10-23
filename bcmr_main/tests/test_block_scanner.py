from unittest import mock

import pytest

from bcmr_main.management.commands import block_scanner as bs
from bcmr_main.models import BlockScan


def make_tx(txid):
    return {'txid': txid, 'vin': [], 'vout': []}


@pytest.mark.django_db
class TestBlockScannerResume:

    def test_starts_at_activation_block_when_nothing_scanned(self):
        command = bs.Command()

        assert command.get_current_block(792773) == 792773

    def test_resumes_from_highest_scanned_block(self):
        BlockScan.objects.create(height=800000, scanned=True)
        BlockScan.objects.create(height=800001, scanned=True)
        command = bs.Command()

        assert command.get_current_block(792773) == 800002

    def test_incomplete_block_below_progress_does_not_reset_progress(self):
        # A half-scanned block must not drag the scanner backwards, otherwise
        # every restart rescans from there.
        BlockScan.objects.create(height=800000, scanned=True)
        BlockScan.objects.create(height=799999, scanned=False)
        command = bs.Command()

        assert command.get_current_block(792773) == 800001


@pytest.mark.django_db
class TestBlockScannerFailureHandling:

    def test_unfetchable_block_is_retried_and_not_recorded(self):
        command = bs.Command()
        node = mock.Mock()
        node.get_block.return_value = None

        assert command.scan_block(node, 800010) is False
        assert BlockScan.objects.filter(height=800010).count() == 0

    def test_failed_tx_keeps_block_unscanned_and_creates_no_duplicate(self):
        command = bs.Command()
        node = mock.Mock()
        node.get_block.return_value = [make_tx('aa'), make_tx('bb')]

        def flaky(tx):
            if tx['txid'] == 'bb':
                raise ValueError('boom')

        with mock.patch.object(bs, 'process_tx', side_effect=flaky):
            assert command.scan_block(node, 800020) is False

        rows = BlockScan.objects.filter(height=800020)
        assert rows.count() == 1
        assert rows.first().scanned is False

    def test_retry_completes_block_in_single_row(self):
        command = bs.Command()
        node = mock.Mock()
        node.get_block.return_value = [make_tx('aa'), make_tx('bb')]

        def flaky(tx):
            if tx['txid'] == 'bb':
                raise ValueError('boom')

        with mock.patch.object(bs, 'process_tx', side_effect=flaky):
            command.scan_block(node, 800030)

        with mock.patch.object(bs, 'process_tx', return_value=None) as ok:
            assert command.scan_block(node, 800030) is True
            # The whole block is replayed so the previously failed tx is retried.
            assert ok.call_count == 2

        rows = BlockScan.objects.filter(height=800030)
        assert rows.count() == 1
        row = rows.first()
        assert row.scanned is True
        assert row.scan_completed is not None

    def test_gives_up_after_max_attempts_so_scanning_can_advance(self):
        command = bs.Command()
        node = mock.Mock()
        node.get_block.return_value = [make_tx('bb')]

        with mock.patch.object(bs, 'process_tx', side_effect=ValueError('always')):
            results = [
                command.scan_block(node, 800040)
                for _ in range(bs.MAX_BLOCK_ATTEMPTS)
            ]

        assert results[:-1] == [False] * (bs.MAX_BLOCK_ATTEMPTS - 1)
        assert results[-1] is True
        assert BlockScan.objects.get(height=800040).scanned is True

    def test_attempt_counter_is_per_block(self):
        command = bs.Command()
        node = mock.Mock()
        node.get_block.return_value = [make_tx('bb')]

        with mock.patch.object(bs, 'process_tx', side_effect=ValueError('boom')):
            command.scan_block(node, 800050)
            command.scan_block(node, 800050)

        command._attempts.pop(800050, None)
        with mock.patch.object(bs, 'process_tx', side_effect=ValueError('boom')):
            assert command.scan_block(node, 800050) is False
