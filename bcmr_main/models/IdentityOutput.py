from django.utils import timezone
from django.db import models

from bcmr_main.models.Token import Token


class IdentityOutput(models.Model):
    txid = models.CharField(max_length=255)
    index = models.PositiveIntegerField()
    block = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    token = models.ForeignKey(
        Token,
        related_name='outputs',
        on_delete=models.CASCADE
    )

    authbase = models.BooleanField(default=False)
    genesis = models.BooleanField(default=False)
    spent = models.BooleanField(default=False)

    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Identity Outputs'
        ordering = ('-date_created', )
        unique_together = (
            'txid',
            'index',
        )
