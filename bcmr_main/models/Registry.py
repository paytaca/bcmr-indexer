from django.db import models
from django.utils import timezone


class Registry(models.Model):
    category = models.CharField(max_length=255, unique=True, primary_key=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
