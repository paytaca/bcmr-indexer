from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry

class NftType(APIView):
    """
    Returns the NftType(s) of a particular NftCategory
    """
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        commitment = kwargs.get('commitment', '')
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')
        registry = Registry.find_registry_by_token_category(category)
        if registry:
            r = Registry.objects.get(id=registry['registry_id'])
            if r:
                if commitment:
                    return JsonResponse(r.get_nft_type(category, commitment), safe=False)
                else:
                    return JsonResponse(r.get_nft_types(category, int(limit or 2), int(offset or 0)), safe=False)
        return JsonResponse(data=None, safe=False)
