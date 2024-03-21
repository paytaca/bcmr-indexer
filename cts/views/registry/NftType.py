from rest_framework.views import APIView
from django.http import JsonResponse
from ...registrycontenthelpers import get_nft_type, get_nft_types

class NftType(APIView):
    allowed_methods = ['GET']
    """
    Returns the NftType(s) of a particular NftCategory
    """
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        commitment = kwargs.get('commitment', '')
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')
        paginated = request.query_params.get('paginated')
        if (paginated or '').lower() == 'true':
            paginated = True
        else:
            paginated = False
        if commitment:
            return JsonResponse(get_nft_type(category, commitment), safe=False)
        else:
            return JsonResponse(get_nft_types(category, int(limit or 10), int(offset or 0), paginated, request.get_raw_uri().split('?')[0]), safe=False)
