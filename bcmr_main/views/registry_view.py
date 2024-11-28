from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from bcmr_main.models import Registry
from decouple import config
import redis
import json

class RegistryView(APIView):
    
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        if not category:
            return JsonResponse(data=None, safe=False)
        
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        cache_key = f'registry:token:{category}'
        cached_response = client.get(cache_key)
        if cached_response:
            response = json.loads(cached_response)
        else:
            try:
                registry = Registry.objects.filter(contents__identities__has_key=category, publisher__identities__contains=[category]).latest('publisher_id')
                response = registry.contents
                client.set(cache_key, json.dumps(response), ex=(60 * 60 * 24))
            except Registry.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return JsonResponse(response, safe=False)
