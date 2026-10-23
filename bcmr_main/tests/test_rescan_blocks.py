from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from bcmr_main.management.commands.rescan_blocks import Command
from bcmr_main.models import BlockScan


def make_tx(txid):
    return {'txid': txid, 'vin': [], 'vout': []}


@pytest.mark.django_db
class TestRescanBlocks:

    def test_reprocesses_an_already_scanned_block(self):
        # A block that was marked scanned after its transactions failed.
        BlockScan.objects.create(height=951147, scanned=True)

        node = mock.Mock()
        node.get_latest_block.return_value = 960000
        node.get_block.return_value = [make_tx('aa'), make_tx('bb')]

        with mock.patch('bcmr_main.management.commands.rescan_blocks.BCHN',
                        return_value=node), \
             mock.patch('bcmr_main.management.commands.rescan_blocks.process_tx') as process:
            call_command('rescan_blocks', '--start', '951147', '--end', '951147')

        assert process.call_count == 2
        assert BlockScan.objects.filter(height=951147).count() == 1

    def test_dry_run_saves_nothing(self):
        node = mock.Mock()
        node.get_latest_block.return_value = 960000
        node.get_block.return_value = [make_tx('aa')]

        with mock.patch('bcmr_main.management.commands.rescan_blocks.BCHN',
                        return_value=node), \
             mock.patch('bcmr_main.management.commands.rescan_blocks.process_tx') as process:
            call_command('rescan_blocks', '--start', '951147', '--end', '951147',
                         '--dry-run')

        assert process.call_count == 0
        assert BlockScan.objects.count() == 0

    def test_rejects_inverted_range(self):
        with pytest.raises(CommandError):
            call_command('rescan_blocks', '--start', '10', '--end', '5')

    def test_rejects_range_above_chain_tip(self):
        node = mock.Mock()
        node.get_latest_block.return_value = 100

        with mock.patch('bcmr_main.management.commands.rescan_blocks.BCHN',
                        return_value=node):
            with pytest.raises(CommandError):
                call_command('rescan_blocks', '--start', '50', '--end', '200')

    def test_raises_when_a_transaction_keeps_failing(self):
        node = mock.Mock()
        node.get_latest_block.return_value = 960000
        node.get_block.return_value = [make_tx('aa')]

        with mock.patch('bcmr_main.management.commands.rescan_blocks.BCHN',
                        return_value=node), \
             mock.patch('bcmr_main.management.commands.rescan_blocks.process_tx',
                        side_effect=ValueError('boom')):
            with pytest.raises(CommandError):
                call_command('rescan_blocks', '--start', '951147', '--end', '951147')
