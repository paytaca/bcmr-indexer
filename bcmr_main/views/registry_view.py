from rest_framework.views import APIView

from django.http import JsonResponse

from bcmr_main.models import Registry


class RegistryView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')

        registries = Registry.objects.filter(category=category)

        if registries.exists():
            registry = registries.first()
            if registry.metadata:
                metadata = registry.metadata
                metadata['$schema'] = 'https://cashtokens.org/bcmr-v2.schema.json'
                metadata['license'] = 'CC0-1.0'
                return JsonResponse(metadata)
        raise Registry.DoesNotExist
