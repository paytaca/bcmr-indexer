from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from bcmr_main.serializers import WebhookSerializer
from bcmr_main.tasks import process_op_return


class WebhookViewSet(viewsets.GenericViewSet):
    serializer_class = WebhookSerializer

    @action(methods=['POST'], detail=False)
    def webhook(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)        
        process_op_return.delay(**serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
