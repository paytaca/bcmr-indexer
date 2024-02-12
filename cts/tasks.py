import redis
import json
import datetime
from decouple import config
from celery import shared_task
from bcmr_main.models import Registry

@shared_task()
def update_identity_snapshot_cache(category):
  client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
  registry = Registry.find_registry_id(category)
  if registry:
      r = Registry.objects.get(id=registry['registry_id'])
      if r:
            identity_snapshot = r.get_identity_snapshot_basic(category)
            client.set(f'{category}_identity-snapshot',json.dumps({**identity_snapshot, 'time': datetime.datetime.utcnow()}), ex=(60 * 30))

