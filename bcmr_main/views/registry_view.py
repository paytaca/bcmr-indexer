from rest_framework import viewsets, status
from rest_framework.views import APIView

from django.http import JsonResponse

from bcmr_main.models import Registry


class RegistryView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')

        try:
            registry = Registry.objects.get(category=category)
            return JsonResponse(registry.data)
        except Registry.DoesNotExist as dne:
            return JsonResponse({})
