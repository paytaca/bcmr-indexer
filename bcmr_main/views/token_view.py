from rest_framework import viewsets, mixins

from django_filters import rest_framework as filters

from bcmr_main.serializers import TokenSerializer
from bcmr_main.filters import TokenFilter
from bcmr_main.models import Token


class TokenViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    filterset_class = TokenFilter
    filterset_backends = (
        filters.DjangoFilterBackend,
    )
