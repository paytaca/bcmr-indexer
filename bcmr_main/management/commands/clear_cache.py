from django.core.management.base import BaseCommand
from bcmr_main.utils import get_redis_client


class Command(BaseCommand):
    help = "Clear registries and token metadata cache"

    def add_arguments(self, parser):
        parser.add_argument("category", nargs="+", type=str)

    def handle(self, *args, **options):
        client = get_redis_client()
        keys_to_delete = []
        if options.get('category'):
            category = options.get('category')[0]
            if category == 'all':
                keys_to_delete += client.keys('registry:token:*')
                keys_to_delete += client.keys('registry:*:*')
                keys_to_delete += client.keys('metadata:token:*')
            else:
                # Exact key (no sub-keys) + any wildcard sub-keys
                keys_to_delete += client.keys(f'registry:token:{category}')
                keys_to_delete += client.keys(f'registry:token:{category}:*')
                keys_to_delete += client.keys(f'metadata:token:{category}')
                keys_to_delete += client.keys(f'metadata:token:{category}:*')

        valid_keys = [k for k in keys_to_delete if k is not None]
        if valid_keys:
            client.delete(*valid_keys)

        if category == 'all':
            self.stdout.write('Cache cleared!')
        else:
            self.stdout.write(f'Cache cleared for category: {category}!')
