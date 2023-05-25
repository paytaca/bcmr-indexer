from django.db import models
from django.utils import timezone


class Registry(models.Model):
    category = models.CharField(max_length=255, unique=True, primary_key=True)
    data = models.JSONField(null=True, blank=True)
    latest_revision = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-latest_revision', )
