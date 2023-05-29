from django_filters import rest_framework as filters

from bcmr_main.models import Token


class TokenFilter(filters.FilterSet):
    class Meta:
        model = Token
        fields = (
            'category',
            'is_nft',
        )
