from rest_framework.views import APIView
from django.http import JsonResponse
from ...registrycontenthelpers import get_nfts

class NftCategory(APIView):
    allowed_methods = ['GET']
    """
    Returns the nfts (NftCategory) without the parse.types data.
    """
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        return JsonResponse(get_nfts(category), safe=False)
