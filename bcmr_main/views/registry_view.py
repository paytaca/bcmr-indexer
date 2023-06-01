from rest_framework.views import APIView

from django.http import JsonResponse

from bcmr_main.models import Registry


class RegistryView(APIView):

    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')

        registries = Registry.objects.filter(category=category)

        if registries.exists():
            registry = registries.first()
            return JsonResponse(registry.metadata)
        return JsonResponse({})
