from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Registry
from bcmr_main.utils import parse_token_info


class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        type_key = kwargs.get('type_key', '')
        try:
            token_info = parse_token_info(category, type_key)
            return JsonResponse(token_info)
        except Registry.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
