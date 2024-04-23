import redis
import json
from rest_framework.views import APIView
from decouple import config
from django.http import JsonResponse
from bcmr_main.models import Registry
from ...registrycontenthelpers import get_token_category_basic
from ...tasks import update_tokencategorymetadata_cache

class TokenCategory(APIView):
    allowed_methods = ['GET']
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        cache_key = f'tokencategorymetadata:{category}'
        token_metadata = client.get(cache_key)
        if token_metadata:
            token_metadata = json.loads(token_metadata)
            update_tokencategorymetadata_cache.delay(category)
            return JsonResponse(token_metadata, safe=False)
        return JsonResponse(get_token_category_basic(category) | {})
