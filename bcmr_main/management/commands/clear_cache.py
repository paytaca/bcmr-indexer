from django.core.management.base import BaseCommand
from decouple import config
import redis

class Command(BaseCommand):
    help = "Clear registries and token metadata cache"

    def add_arguments(self, parser):
        parser.add_argument("category", nargs="+", type=str)

    def handle(self, *args, **options):
        client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
        keys_to_delete = []
        if options.get('category'):
            category = options.get('category')
            if category == 'all':
                registries_keys = 'registry:token:*'
                keys_to_delete += registries_keys
                token_metadata_keys = 'metadata:token:*'
                keys_to_delete += token_metadata_keys
            else:
                registries_keys = f'registry:token:{category}:*'
                keys_to_delete += registries_keys
                token_metadata_keys = f'metadata:token:{category}:*'
                keys_to_delete += token_metadata_keys       

        for key in keys_to_delete:
            client.delete(key)
        if options.get('category') == 'all':
            print('Cache cleared!')
        else:
            print(f'Cache cleared for category: {category}!')
