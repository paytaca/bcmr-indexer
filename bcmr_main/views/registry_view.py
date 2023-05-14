from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView

from bcmr_main.models import Registry, Token
from bcmr_main.serializers import RegistrySerializer


class RegistryView(APIView):

    def get(self, request, *args, **kwargs):
        token_id = kwargs.get('token_id', '')

        try:
            registry = Registry.objects.get(token__category=token_id)
            serializer = RegistrySerializer(registry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Registry.DoesNotExist as dne:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
