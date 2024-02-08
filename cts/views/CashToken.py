from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from bcmr_main.models import Token
from cts.serializers import TokenSerializer

class CashToken(APIView):
    """
    Returns the unique minted tokens
    """
    serializer_class = TokenSerializer

    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        
        nft_type = kwargs.get('nft_type')
        category = kwargs.get('category')
        tokens = Token.objects.all()
        
        if category:
            tokens = tokens.filter(category=category)

        if nft_type == 'fts':
            tokens = tokens.filter(capability__isnull=False)
        elif nft_type == 'nfts':
            tokens = tokens.filter(capability__isnull=True,amount__gt=0)
        elif nft_type == 'hybrids':
            tokens = tokens.filter(capability__isnull=False,amount__gt=0)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_queryset = paginator.paginate_queryset(tokens, request)
        
        serializer = TokenSerializer(paginated_queryset, many=True)
        # paginated_response = paginator.get_paginated_response(serializer.data)        

        return JsonResponse({
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data
        })
    

