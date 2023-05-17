from django.db import models
from django.utils import timezone

from bcmr_main.models.Token import Token


class IdentityOutput(models.Model):
    tx_hash = models.CharField(max_length=100, unique=True, primary_key=True)
    authbase = models.BooleanField(default=False)
    genesis = models.BooleanField(default=False)
    spent = models.BooleanField(default=False)
    burned = models.BooleanField(default=False)
    token = models.ForeignKey(
        Token,
        related_name='identity_output',
        on_delete=models.CASCADE
    )
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = (
            '-date_created',
            'token',
        )
