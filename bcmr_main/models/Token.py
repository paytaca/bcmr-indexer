from django.db import models


class Token(models.Model):
    class Capability(models.TextChoices):
        MINTING = 'minting'
        MUTABLE = 'mutable'
        NONE = 'none'

    category = models.CharField(max_length=70)
    debut_txid = models.CharField(max_length=70, null=True, blank=True)
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
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-date_created', )
        unique_together = (
            'category',
            'commitment',
            'capability',
        )
        indexes = [
            models.Index(fields=['category', 'commitment', 'capability', 'is_nft'])
        ]
