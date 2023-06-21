from django.db import models


class Token(models.Model):
    class Capability(models.TextChoices):
        MINTING = 'minting'
        MUTABLE = 'mutable'
        NONE = 'none'

    category = models.CharField(max_length=70)
    debut_txid = models.CharField(max_length=70, null=True, blank=True)
    amount = models.BigIntegerField(null=True)
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
        ordering = ('-id', )
        unique_together = (
            'category',
            'commitment',
            'capability',
        )
        indexes = [
            models.Index(
                fields=[
                    'category',
                    'commitment',
                    'capability',
                    'is_nft'
                ]
            )
        ]

    def __str__(self):
        fields = [self.category, self.commitment, self.capability]
        return '|'.join([x for x in fields if x])


class TokenMetadata(models.Model):

    class MetadataType(models.TextChoices):
        CATEGORY = 'category'
        TYPE = 'type'

    token = models.ForeignKey(
        'Token',
        related_name='metadata',
        on_delete=models.CASCADE
    )
    identity = models.ForeignKey(
        'IdentityOutput',
        related_name='tokens_created',
        on_delete=models.CASCADE
    )
    registry = models.ForeignKey(
        'Registry',
        related_name='token_metadata',
        on_delete=models.CASCADE
    )
    metadata_type = models.CharField(
        max_length=20,
        choices=MetadataType.choices,
        null=True,
        blank=True
    )
    contents = models.JSONField(null=True, blank=True)
    date_created = models.DateTimeField(null=True)

    class Meta:
        verbose_name_plural = 'Token metadata'
        get_latest_by = 'date_created'
        unique_together = (
            'token',
            'identity',
            'registry',
            'metadata_type'
        )
        indexes = [
            models.Index(
                fields=[
                    'metadata_type',
                    'date_created'
                ]
            )
        ]
