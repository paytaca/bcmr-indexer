from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry

class TokenCategory(APIView):
    allowed_methods = ['GET']
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        registry = Registry.find_registry_by_token_category(category)
        # return JsonResponse(registry)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                return JsonResponse(r.get_token_category_basic(category) | {})
        return JsonResponse(data=None, safe=False)
