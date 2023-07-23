from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from bcmr_main.bchn import BCHN
from bcmr_main.tasks import process_tx
from bcmr_main.models import *
import logging


LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Rescan blocks to record missed transactions since first cashtoken block"

    def handle(self, *args, **options):
        # NOTE: uncomment for testing
        # Token.objects.all().delete()
        # TokenMetadata.objects.all().delete()
        # Registry.objects.all().delete()
        # IdentityOutput.objects.all().delete()
        # BlockScan.objects.all().delete()
        # Ownership.objects.all().delete()

        LOGGER.info('STARTING RESCANNING OF BLOCKS')

        node = BCHN()
        latest_block = node.get_latest_block()

        curr_block = 792773
        if settings.NETWORK == 'chipnet':
            curr_block = 120000

        scanned_blocks = BlockScan.objects.filter(scanned=True)
        if scanned_blocks.exists():
            curr_block = scanned_blocks.latest('height').height
            
        while curr_block <= latest_block:
            LOGGER.info(f'Obtaining block data for #{curr_block}...')
            transactions = node.get_block(curr_block)
            total_txs = len(transactions)
            block_scan, _ = BlockScan.objects.get_or_create(
                height=curr_block,
                transactions=total_txs
            )
            block_scan.scan_started = timezone.now()

            LOGGER.info(f'Block: {curr_block}  |  Transactions: {total_txs}')

            for i, txid in enumerate(transactions, 1):
                try:
                    LOGGER.info(f'    {curr_block} | {txid} | {i} of {total_txs}')
                    process_tx(txid, block_txns=transactions)
                except Exception as exc:
                    LOGGER.error(f'Error processing txid: {txid}')
                    raise exc
                
            block_scan.scan_completed = timezone.now()
            block_scan.scanned = True
            block_scan.save()

            curr_block += 1

        LOGGER.info('Rescanning block tasks queued!')
