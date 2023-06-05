from django.db import models
from django.utils import timezone


class Registry(models.Model):
    category = models.CharField(max_length=255)
    txid = models.CharField(max_length=255, default='')
    metadata = models.JSONField(null=True, blank=True)
    valid = models.BooleanField(default=False)
    op_return = models.TextField(default='')
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
