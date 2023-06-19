from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import BlockScan


class LatestBlockView(APIView):

    def get(self, request, *args, **kwargs):
        latest_block = BlockScan.objects.filter(scanned=True).latest('height')
        return JsonResponse({'height': latest_block.height})
