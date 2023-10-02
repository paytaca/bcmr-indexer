from django.db import models
from django.utils import timezone


class Registry(models.Model):
    publisher = models.CharField(max_length=100)
    contents = models.JSONField(null=True, blank=True)
    bcmr_url = models.TextField(default='')
    bcmr_request_status = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-last_updated', '-date_created')
