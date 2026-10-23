from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Max
from django.utils import timezone
from bcmr_main.bchn import BCHN
from bcmr_main.tasks import process_tx
from bcmr_main.models import *
import logging
import time


LOGGER = logging.getLogger(__name__)

# How many times a single block is retried after one of its transactions
# fails, before it is marked as scanned and the failures are logged.
MAX_BLOCK_ATTEMPTS = 5

# Seconds to wait before polling for new blocks again.
POLL_INTERVAL = 10


class Command(BaseCommand):
    help = "Block scanner"

    def get_current_block(self, ct_activation_block):
        """Return the next block height that still needs to be scanned."""
        latest_scanned = BlockScan.objects.filter(scanned=True).aggregate(
            max_height=Max('height')
        )['max_height']

        if latest_scanned is not None:
            return latest_scanned + 1
        return ct_activation_block

    def scan_block(self, node, height):
        """
        Scan a single block. Returns True when the block is complete (either
        scanned or permanently skipped), False when it should be retried.
        """
        transactions = node.get_block(height)
        if transactions is None:
            LOGGER.warning(
                'Could not fetch block #%s, will retry later.', height
            )
            return False

        total_txs = len(transactions)

        # Look up on height alone. The previous version also matched on
        # `transactions`, so a retried block created a duplicate row.
        block_scan = (
            BlockScan.objects.filter(height=height, scanned=False).order_by('-id').first()
        )
        if block_scan is None:
            block_scan = BlockScan(height=height, scan_started=timezone.now())
        block_scan.transactions = total_txs
        block_scan.save()

        LOGGER.info('Block: %s  |  Transactions: %s', height, total_txs)

        failed = []
        for i, tx in enumerate(transactions, 1):
            txid = tx.get('txid')
            try:
                LOGGER.info('    %s | %s | %s of %s', height, txid, i, total_txs)
                process_tx(tx)
            except Exception:
                # A single bad transaction must not take down the scanner and
                # restart the whole process, which used to loop on the same
                # block forever.
                LOGGER.exception(
                    'Error processing txid %s in block #%s', txid, height
                )
                failed.append(txid)

        if failed:
            attempts = getattr(self, '_attempts', {})
            attempts[height] = attempts.get(height, 0) + 1
            self._attempts = attempts

            if attempts[height] < MAX_BLOCK_ATTEMPTS:
                LOGGER.warning(
                    'Block #%s had %s failed tx(s), retrying (%s/%s).',
                    height, len(failed), attempts[height], MAX_BLOCK_ATTEMPTS
                )
                return False

            LOGGER.error(
                'Giving up on block #%s after %s attempts. Failed txids: %s',
                height, MAX_BLOCK_ATTEMPTS, failed
            )

        block_scan.scan_completed = timezone.now()
        block_scan.scanned = True
        block_scan.save()

        # clear the queued transactions table
        QueuedTransaction.objects.all().delete()
        return True

    def handle(self, *args, **options):

        LOGGER.info('STARTING BLOCK SCANNER...')
        node = BCHN()

        ct_activation_block = 792773
        if settings.NETWORK == 'chipnet':
            ct_activation_block = 120000
            # ct_activation_block = 186438

        self._attempts = {}

        while True:
            try:
                latest_block = node.get_latest_block()
            except Exception:
                # The node (or its SSH tunnel) can be briefly unreachable.
                # Retrying beats being restarted by supervisord.
                LOGGER.exception(
                    'Could not get latest block height, retrying in %ss.',
                    POLL_INTERVAL
                )
                time.sleep(POLL_INTERVAL)
                continue

            if latest_block is None:
                LOGGER.warning(
                    'Latest block height unavailable, retrying in %ss.',
                    POLL_INTERVAL
                )
                time.sleep(POLL_INTERVAL)
                continue

            current_block = self.get_current_block(ct_activation_block)

            if current_block > latest_block:
                LOGGER.info(
                    'No new block...checking again in %ss...', POLL_INTERVAL
                )
                time.sleep(POLL_INTERVAL)
                continue

            while current_block <= latest_block:
                LOGGER.info('Obtaining block data for #%s...', current_block)

                if not self.scan_block(node, current_block):
                    # Block not finished (RPC hiccup or failed tx). Leave the
                    # height unscanned so it is retried on the next pass.
                    break

                self._attempts.pop(current_block, None)
                current_block += 1

            time.sleep(POLL_INTERVAL)
