from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry

class IdentitySnapshot(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        registry = Registry.find_registry_by_token_category(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                return JsonResponse(r.get_identity_snapshot(category) | {})
        return JsonResponse(data=None, safe=False)
