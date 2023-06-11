from django.db import models
from bcmr_main.models import Token


class Ownership(models.Model):
    token = models.ForeignKey(
        Token,
        related_name='ownership_history',
        on_delete=models.CASCADE
    )
    address = models.CharField(max_length=100, null=True, blank=True)
    txid = models.CharField(max_length=255, unique=True)
    date_acquired = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-date_acquired',)
        indexes = [
            models.Index(fields=['address'])
        ]
