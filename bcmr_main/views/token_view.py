from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from bcmr_main.models import Token, TokenMetadata


class TokenView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        type_key = kwargs.get('type_key', '')
        try:
            if type_key:
                token = Token.objects.get(
                    category=category,
                    commitment=type_key,
                    capability='none'
                )
            else:
                token = Token.objects.get(
                    category=category,
                    commitment=None
                )
            token_metadata = TokenMetadata.objects.filter(token=token).order_by('date_created').last()
            if token_metadata:
                response = token_metadata.contents
                if isinstance(response, list):
                    response = response[0]
                return JsonResponse(response)
        except Token.DoesNotExist:
            pass
        
        return Response(status=status.HTTP_404_NOT_FOUND)
