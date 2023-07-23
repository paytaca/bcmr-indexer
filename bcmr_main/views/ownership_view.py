from rest_framework import viewsets

from django.conf import settings
from django_filters import rest_framework as filters

from bcmr_main.serializers import OwnershipSerializer
from bcmr_main.models import Ownership
from bcmr_main.filters import OwnershipFilter


class OwnershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OwnershipSerializer
    queryset = Ownership.objects.order_by('-date_acquired', '-id')
    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = OwnershipFilter
