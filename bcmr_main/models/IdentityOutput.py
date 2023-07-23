from django.db import models
from django.contrib.postgres.fields import ArrayField


class IdentityOutput(models.Model):
    txid = models.CharField(max_length=100, unique=True)
    block = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=128, null=True, blank=True)
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
    identities = ArrayField(
        models.CharField(max_length=70), null=True, blank=True
    )
    date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Identity Outputs'
        ordering = ('-id', )
        indexes = [
            models.Index(fields=['txid', 'spent', 'authbase'])
        ]

    def _retrieve_identities(self, parents, identities=[]):
        _parents = []
        if parents:
            # Check if parents already have identities
            identities_check = parents.filter(identities__isnull=False)
            if identities_check.count() == parents.count():
                _parents = []
                for child in identities_check:
                    identities += child.identities
            else:
                authbases1 = parents.filter(authbase=True)
                ancestors = IdentityOutput.objects.filter(spender__in=parents)
                authbases2 = ancestors.filter(authbase=True)
                authbases = authbases1 | authbases2
                identities += [x.txid for x in authbases]
                _parents = ancestors.filter(authbase=False)
            return self._retrieve_identities(_parents, identities)
        else:
            return identities

    def get_identities(self):
        identities = []
        if self.authbase:
            identities = [self.txid]
        else:
            if self.identities:
                identities = self.identities        
            else:
                parents = IdentityOutput.objects.filter(spender__txid=self.txid)
                authbase_counts = [x.authbase for x in parents]
                if parents.count() == authbase_counts.count(True):
                    identities = [x.txid for x in parents]
                else:
                    identities = self._retrieve_identities(parents, [])
        identities = list(set(identities))  # uniquify the list
        # save identities
        for identity in identities:
            identity_obj = IdentityOutput.objects.get(txid=identity)
            self.identities.add(identity_obj)
        return identities
