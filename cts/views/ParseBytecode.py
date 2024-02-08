from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry

class ParseBytecode(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        registry = Registry.find_registry_by_token_category(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                token_category = r.get_token_category_basic(category)
                if token_category.get('meta'):
                  meta = token_category.get('meta')
                  return JsonResponse(r.get_parse_bytecode(meta.get('authbase'), meta.get('identity_history')), safe=False)
        return JsonResponse(data=None, safe=False)
