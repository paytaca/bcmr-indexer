from django.db import models
from django.utils import timezone


class Token(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active'
        INACTIVE = 'inactive'
        BURNED = 'burned'

    category = models.CharField(max_length=255, primary_key=True, unique=True)
    name = models.CharField(max_length=255, default='', blank=True)
    description = models.TextField(default='', blank=True)
    symbol = models.CharField(max_length=100, default='', blank=True)
    decimals = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=255, default='', blank=True)
    is_nft = models.BooleanField(default=False)

    # see https://github.com/bitjson/chip-bcmr/blob/master/bcmr-v2.schema.ts
    nfts = models.JSONField(null=True, blank=True)

    bcmr_json = models.JSONField(null=True, blank=True)
    bcmr_url = models.URLField(null=True, blank=True)

    updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        ordering = (
            'name',
            'symbol',
            'is_nft',
        )

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super(Token, self).save(*args, **kwargs)
