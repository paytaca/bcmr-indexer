from django.db import models
from django.contrib.postgres.fields import ArrayField

from bcmr_main.models import Token


class Ownership(models.Model):
    token = models.ForeignKey(
        Token,
        related_name='ownership_history',
        on_delete=models.CASCADE
    )
    address = models.CharField(max_length=128, null=True, blank=True)
    txid = models.CharField(max_length=100, unique=True)
    index = models.IntegerField(null=True)
    amount = models.BigIntegerField(null=True, blank=True)
    value = models.BigIntegerField(null=True, blank=True)
    date_acquired = models.DateTimeField(null=True, blank=True)
    spent = models.BooleanField(default=False)
    spender = models.CharField(max_length=128, null=True)
    burned = models.BooleanField(default=False)
    burner = models.CharField(max_length=128, null=True)

    class Meta:
        ordering = ('-date_acquired',)
        unique_together = (
            'txid',
            'token'
        )
        ordering = ('-date_acquired', )
        unique_together = (
            'txid',
            'index',
        )
        indexes = [
            models.Index(fields=['address', 'spent', 'burned'])
        ]
