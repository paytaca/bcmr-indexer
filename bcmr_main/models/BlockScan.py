from django.db import models


class BlockScan(models.Model):
    height = models.IntegerField(default=1, db_index=True)
    transactions = models.IntegerField(default=0)
    scan_started = models.DateTimeField(null=True)
    scan_completed = models.DateTimeField(null=True)
    scanned = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        status = 'PEDNING'
        if self.scan_started:
            status = 'STARTED'
        if self.scan_completed:
            status = 'COMPLETED'
        return f'Block Height: #{self.height} | {status}'
