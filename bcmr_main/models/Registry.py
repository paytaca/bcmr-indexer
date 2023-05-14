from django.db import models
from django.utils import timezone

from bcmr_main.models.Token import Token


class Registry(models.Model):
    version = models.JSONField(default=dict)
    registry_identity = models.JSONField(default=dict)
    latest_revision = models.DateTimeField(null=True, blank=True)
    token = models.OneToOneField(
        Token,
        on_delete=models.CASCADE,
        related_name='registry'
    )

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-latest_revision', )
