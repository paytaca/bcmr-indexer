from django.db import models
from bcmr_main.models import Token


class Ownership(models.Model):
    # ACQUISITION_METHODS = [
    #     ('minting', 'MINTING')
    # ]

    class AcquisitionMethod(models.TextChoices):
        TRANSFER = 'transfer'
        MINTING = 'minting'
        MUTATION = 'mutation'

    token = models.ForeignKey(
        Token,
        related_name='ownership_history',
        on_delete=models.CASCADE
    )
    address = models.CharField(max_length=128, null=True, blank=True)
    amount = models.BigIntegerField()
    txid = models.CharField(max_length=100)
    index = models.IntegerField(null=True)
    date_acquired = models.DateTimeField(null=True, blank=True)
    acquired_via = models.CharField(
        choices=AcquisitionMethod.choices,
        max_length=20,
        db_index=True
    )
    spent = models.BooleanField(default=False)
    spender_txid = models.CharField(max_length=100, null=True)
    burned = models.BooleanField(default=False)

    class Meta:
        ordering = ('-date_acquired',)
        indexes = [
            models.Index(fields=['address', 'spent', 'burned'])
        ]
        unique_together = [ 'token_id', 'txid', 'index' ]
