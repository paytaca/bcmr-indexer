from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import BlockScan


class LatestBlockView(APIView):

    def get(self, request, *args, **kwargs):
        latest_block = BlockScan.objects.filter(scanned=True).order_by('-height').first()
        if not latest_block:
            return JsonResponse({'height': None, 'error': 'no blocks scanned yet'})
        return JsonResponse({'height': latest_block.height})
