from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from bcmr_main.bchn import BCHN
from bcmr_main.tasks import process_tx
from bcmr_main.models import *

class Command(BaseCommand):
    help = "Rescan blocks to record missed transactions since first cashtoken block"

    def handle(self, *args, **options):
        # NOTE: uncomment for testing
        # Token.objects.all().delete()
        # Registry.objects.all().delete()
        # IdentityOutput.objects.all().delete()
        
        node = BCHN()
        latest_block = node.get_latest_block()

        curr_block = 792773
        if settings.NETWORK == 'chipnet':
            curr_block = 120000
            
        while curr_block < latest_block:
            transactions = node.get_block(curr_block)
            self.stdout.write(f'Block: {curr_block}  |  Transactions: {len(transactions)}')

            for txid in transactions:
                process_tx.delay(txid, block_txns=transactions)

            curr_block += 1

        self.stdout.write(self.style.SUCCESS('Rescanning block tasks queued!'))
