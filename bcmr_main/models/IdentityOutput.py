from django.db import models


class IdentityOutput(models.Model):
    txid = models.CharField(max_length=70, unique=True)
    block = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=60, null=True, blank=True)
    authbase = models.BooleanField(default=False)
    genesis = models.BooleanField(default=False)
    spent = models.BooleanField(default=False)
    spender = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True
    )
    date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Identity Outputs'
        ordering = ('-id', )
        indexes = [
            models.Index(fields=['txid', 'spent'])
        ]
