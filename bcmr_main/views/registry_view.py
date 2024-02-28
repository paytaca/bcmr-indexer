from rest_framework.views import APIView
from django.http import JsonResponse
from bcmr_main.models import Registry

class RegistryView(APIView):
    
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        if not category:
            return JsonResponse(data=None, safe=False)

        registry = Registry.objects.filter(contents__identities__has_key=category).latest('id')
        return JsonResponse(data=registry.contents, safe=False)
