from django.db import models
from django.utils import timezone

from bcmr_main.models.Registry import Registry


class Token(models.Model):
    class Capability(models.TextChoices):
        MINTING = 'minting'
        MUTABLE = 'mutable'
        NONE = 'none'

    category = models.CharField(max_length=255)
    amount = models.BigIntegerField(default=0)
    is_nft = models.BooleanField(default=False)
    commitment = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    capability = models.CharField(
        max_length=20,
        choices=Capability.choices,
        null=True,
        blank=True
    )
    registry = models.ForeignKey(
        Registry,
        on_delete=models.CASCADE,
        related_name='tokens',
        null=True,
        blank=True
    )
    bcmr_url = models.URLField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-updated_at', )
        unique_together = (
            'category',
            'commitment',
        )

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super(Token, self).save(*args, **kwargs)
