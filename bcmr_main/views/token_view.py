from rest_framework.views import APIView

from django.http import JsonResponse

from bcmr_main.utils import parse_token_info


class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        type_key = kwargs.get('type_key', '')
        token_info = parse_token_info(category, type_key)
        return JsonResponse(token_info)
