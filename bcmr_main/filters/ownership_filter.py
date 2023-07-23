from django_filters import rest_framework as filters

from bcmr_main.models import Ownership


class OwnershipFilter(filters.FilterSet):
    class Meta:
        model = Ownership
        fields = (
            'token__category',
            'token__capability',
            'token__commitment',
            'address',
            'txid',
        )
