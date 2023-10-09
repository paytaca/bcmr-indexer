from django.db import models


class Registry(models.Model):
    txid = models.CharField(max_length=100)
    index = models.IntegerField()
    publisher = models.ForeignKey(
        'IdentityOutput',
        related_name='registries',
        on_delete=models.CASCADE,
        null=True
    )
    contents = models.JSONField(null=True, blank=True)
    valid = models.BooleanField(default=False)
    op_return = models.TextField(default='')
    bcmr_url = models.TextField(default='')
    bcmr_request_status = models.IntegerField(null=True, blank=True)
    validity_checks = models.JSONField(null=True, blank=True)
    allow_hash_mismatch = models.BooleanField(default=False)
    date_created = models.DateTimeField(null=True, blank=True)
    generated_metadata = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
        indexes = [
            models.Index(fields=[
                'txid',
                'index',
                'valid',
                'date_created',
                'generated_metadata'
            ])
        ]
        unique_together = [
            'txid',
            'index',
            'publisher'
        ]
