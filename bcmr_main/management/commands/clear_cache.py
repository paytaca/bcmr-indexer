from django.core.management.base import BaseCommand
from decouple import config
import redis

class Command(BaseCommand):
    help = "Clear registries and token metadata cache"

    def handle(self, *args, **options):
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        registries_keys = 'registry:token:*'
        client.delete(registries_keys)
        token_metadata_keys = 'metadata:token:*'
        client.delete(token_metadata_keys)
        print('Cache cleared!')