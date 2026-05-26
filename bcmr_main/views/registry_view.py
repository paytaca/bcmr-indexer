from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from bcmr_main.models import Registry
from bcmr_main.utils import get_redis_client
import json
import hashlib


def _etag_for(body: bytes) -> str:
    return hashlib.md5(body).hexdigest()


def _json_response_with_cache_headers(data: dict, max_age: int = 3600) -> JsonResponse:
    """Return a JsonResponse with ETag and Cache-Control headers."""
    body = json.dumps(data, separators=(',', ':')).encode()
    etag = _etag_for(body)
    response = JsonResponse(data, safe=False, json_dumps_params={'separators': (',', ':')})
    response['ETag'] = f'"{etag}"'
    response['Cache-Control'] = f'public, max-age={max_age}'
    return response


class RegistryView(APIView):

    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        if not category:
            return JsonResponse(data=None, safe=False)

        client = get_redis_client()
        cache_key = f'registry:token:{category}'
        cached_response = client.get(cache_key)
        if cached_response:
            response = json.loads(cached_response)
        else:
            try:
                registry = Registry.objects.filter(
                    contents__identities__has_key=category,
                    publisher__identities__contains=[category]
                ).latest('publisher_id')
                response = registry.contents
                client.set(cache_key, json.dumps(response), ex=(60 * 60 * 24))
            except Registry.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        resp = _json_response_with_cache_headers(response)

        # Honour conditional GET — avoid re-sending the full payload if unchanged.
        if request.META.get('HTTP_IF_NONE_MATCH') == resp['ETag']:
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        return resp


class RegistryTxoView(APIView):

    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        txid = kwargs.get('txid', '')
        vout = int(kwargs.get('vout', -1))

        if not txid or vout < 0:
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        client = get_redis_client()
        cache_key = f'registry:{txid}:{vout}'
        cached_response = client.get(cache_key)
        if cached_response:
            response = json.loads(cached_response)
        else:
            try:
                registry = Registry.objects.filter(txid__exact=txid, index__exact=vout).latest('id')
                response = registry.contents
                client.set(cache_key, json.dumps(response), ex=(60 * 60 * 24))
            except Registry.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        resp = _json_response_with_cache_headers(response)

        if request.META.get('HTTP_IF_NONE_MATCH') == resp['ETag']:
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        return resp
