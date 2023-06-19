from django.db import models


class Registry(models.Model):
    txid = models.CharField(max_length=70)
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
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
        indexes = [
            models.Index(fields=['txid', 'index', 'valid', 'date_created'])
        ]
        unique_together = [
            'txid',
            'index',
            'publisher'
        ]

    # def revalidate_identities(self):
    #     validity_checks = self.validity_checks
    #     publisher_identities = self.publisher.identities
    #     matched_identities = set(self.contents['identities'].keys()).intersection(set(publisher_identities))
    #     if matched_identities:
    #         validity_checks['identities_match'] = True
    #     is_valid = list(validity_checks.values()).count(True) == len(validity_checks.keys())
    #     self.valid = is_valid
    #     self.validity_checks = validity_checks
    #     self.save()
