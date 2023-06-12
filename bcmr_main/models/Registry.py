from django.db import models


class Registry(models.Model):
    txid = models.CharField(max_length=70, unique=True)
    index = models.IntegerField()
    category = models.CharField(max_length=70)
    publisher = models.ForeignKey(
        'IdentityOutput',
        related_name='registries',
        on_delete=models.CASCADE,
        null=True
    )
    metadata = models.JSONField(null=True, blank=True)
    valid = models.BooleanField(default=False)
    op_return = models.TextField(default='')
    bcmr_url = models.TextField(default='')
    bcmr_request_status = models.IntegerField(null=True, blank=True)
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
        indexes = [
            models.Index(fields=['category', 'valid'])
        ]