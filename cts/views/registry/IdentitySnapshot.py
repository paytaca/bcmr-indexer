from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry

class IdentitySnapshot(APIView):
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        include_token = request.query_params.get('include_token', '')
        registry = Registry.find_registry_id(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                if include_token and include_token.lower() == 'true':
                    return JsonResponse(r.get_identity_snapshot(category) | {})
                return JsonResponse(r.get_identity_snapshot_basic(category) | {})
                
        return JsonResponse(data=None, safe=False)
