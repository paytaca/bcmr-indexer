from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from bcmr_main.bchn import BCHN
from bcmr_main.models import BlockScan
from bcmr_main.tasks import process_tx

import logging


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Re-process an inclusive range of block heights, ignoring the current "
        "BlockScan state. Use this to recover blocks that were marked scanned "
        "after transactions failed (see 'Giving up on block #' in the logs), "
        "for example after fixing the bug that caused the failure."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--start', type=int, required=True, help='First block height (inclusive).'
        )
        parser.add_argument(
            '--end', type=int, required=True, help='Last block height (inclusive).'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Resolve and count transactions without saving anything.',
        )

    def handle(self, *args, **options):
        start = options['start']
        end = options['end']
        dry_run = options['dry_run']

        if start > end:
            raise CommandError('--start must be less than or equal to --end')

        node = BCHN()
        latest_block = node.get_latest_block()
        if latest_block is None:
            raise CommandError('Could not reach the node to read the chain height')
        if end > latest_block:
            raise CommandError(
                f'--end {end} is above the current chain height {latest_block}'
            )

        LOGGER.info(
            'Rescanning blocks %s..%s%s', start, end,
            ' (dry run)' if dry_run else ''
        )

        failures = {}
        for height in range(start, end + 1):
            transactions = node.get_block(height)
            if transactions is None:
                # Fail loudly: the operator asked for this range explicitly and
                # silently skipping it would hide missing data.
                raise CommandError(f'Could not fetch block #{height}')

            total = len(transactions)
            self.stdout.write(f'Block #{height}: {total} transaction(s)')
            if dry_run:
                continue

            failed = []
            for i, tx in enumerate(transactions, 1):
                txid = tx.get('txid')
                try:
                    LOGGER.info('    %s | %s | %s of %s', height, txid, i, total)
                    process_tx(tx)
                except Exception:
                    LOGGER.exception(
                        'Error processing txid %s in block #%s', txid, height
                    )
                    failed.append(txid)

            block_scan, _ = BlockScan.objects.get_or_create(height=height, scanned=True)
            block_scan.transactions = total
            block_scan.scan_completed = timezone.now()
            block_scan.scanned = True
            block_scan.save()

            if failed:
                failures[height] = failed
                self.stderr.write(
                    f'Block #{height}: {len(failed)} transaction(s) failed'
                )

        if failures:
            self.stderr.write('\nTransactions that still failed:')
            for height, txids in failures.items():
                self.stderr.write(f'  block {height}:')
                for txid in txids:
                    self.stderr.write(f'    {txid}')
            raise CommandError(
                f'{sum(len(v) for v in failures.values())} transaction(s) failed; '
                'see the list above and the log output'
            )

        self.stdout.write(self.style.SUCCESS(f'Rescanned blocks {start}..{end}'))
