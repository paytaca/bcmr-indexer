from django.db import models


class Registry(models.Model):
    category = models.CharField(max_length=255)
    txid = models.CharField(max_length=255, unique=True)
    metadata = models.JSONField(null=True, blank=True)
    valid = models.BooleanField(default=False)
    op_return = models.TextField(default='')
    bcmr_url = models.TextField(default='')
    bcmr_request_status = models.IntegerField(null=True, blank=True)
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
