from django.db import models


class IdentityOutput(models.Model):
    txid = models.CharField(max_length=70, unique=True)
    block = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=70, null=True, blank=True)
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
    identities = models.ManyToManyField(
        'self',
        related_name='identity_outputs'
    )
    date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Identity Outputs'
        ordering = ('-id', )
        indexes = [
            models.Index(fields=['txid', 'spent'])
        ]

    def _retrieve_identities(self, parents, identities=[]):
        _parents = []
        if parents:
            authbases1 = parents.filter(authbase=True)
            ancestors = IdentityOutput.objects.filter(spender__in=parents)
            authbases2 = ancestors.filter(authbase=True)
            authbases = authbases1 | authbases2
            identities += [x.txid for x in authbases]
            _parents = ancestors.filter(authbase=False)
        else:
            return identities
        return self._retrieve_identities(_parents, identities)

    def get_identities(self, save=False):
        if self.identities.all():
            return [x.txid for x in self.identities.all()]
        else:
            parents = IdentityOutput.objects.filter(spender__txid=self.txid)
            identities = self._retrieve_identities(parents)
            if save:
                for identity in identities:
                    identity_obj = IdentityOutput.objects.get(txid=identity)
                    self.identities.add(identity_obj)
            return identities
