from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from bcmr_main.bchn import BCHN
from bcmr_main.tasks import process_tx
from bcmr_main.models import *
import logging
import time


LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Block scanner"

    def handle(self, *args, **options):

        LOGGER.info('STARTING BLOCK SCANNER...')
        node = BCHN()

        ct_activation_block = 792773
        if settings.NETWORK == 'chipnet':
            # ct_activation_block = 120000
            ct_activation_block = 186438
            
        while True:
            latest_block = node.get_latest_block()

            scanned_blocks = BlockScan.objects.filter(scanned=True)
            if scanned_blocks.exists():
                current_block = scanned_blocks.latest('height').height + 1
            else:
                current_block = ct_activation_block

            while current_block <= latest_block:
                LOGGER.info(f'Obtaining block data for #{current_block}...')
                transactions = node.get_block(current_block)
                total_txs = len(transactions)
                block_scan, _ = BlockScan.objects.get_or_create(
                    height=current_block,
                    transactions=total_txs,
                    scan_started=timezone.now(),
                    scan_completed=None,
                )
                LOGGER.info(f'Block: {current_block}  |  Transactions: {total_txs}')

                for i, tx in enumerate(transactions, 1):
                    txid = tx['txid']
                    try:
                        LOGGER.info(f'    {current_block} | {txid} | {i} of {total_txs}')
                        process_tx(tx)
                    except Exception as exc:
                        LOGGER.error(f'Error processing txid: {txid}')
                        raise exc
                    
                block_scan.scan_completed = timezone.now()
                block_scan.scanned = True
                block_scan.save()

                # clear the queued transactions table
                QueuedTransaction.objects.all().delete()

                current_block += 1

            LOGGER.info('No new block...checking again in 10 seconds...')
            time.sleep(10)
