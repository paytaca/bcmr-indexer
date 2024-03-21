import redis
import json
import datetime
from decouple import config
from celery import shared_task
from bcmr_main.models import Registry
from .registrycontenthelpers import (
  get_identity_snapshot_basic,
  get_nft_type,
  get_token_category_basic
)
@shared_task(queue='resolve_metadata')
def update_identity_snapshot_cache(category, cache_key=None):
  client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
  # registry = Registry.find_registry_id(category)
  # if registry:
  #     r = Registry.objects.get(id=registry['registry_id'])
  #     if r:
  #           identity_snapshot = r.get_identity_snapshot_basic(category)
  #           client.set(f'{category}_identity-snapshot',json.dumps(identity_snapshot), ex=(60 * 30))
  identity_snapshot = get_identity_snapshot_basic(category)
  cache_key = cache_key or f'identitysnapshot:{category}'
  if identity_snapshot:
    try:
      client.set(cache_key, json.dumps(identity_snapshot), ex=(60 * 30))
    except Exception as e:
      pass


@shared_task(queue='resolve_metadata')
def update_nftmetadata_cache(category, commitment, cache_key=None):
  client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
  cache_key = cache_key or f'nftmetadata:{category}:{commitment}'  
  # r = Registry.objects.filter(contents__identities__has_key=category)
  # if r.exists():
  #   r = r.latest('id')
  #   metadata = r.get_nft_type(category=category, commitment=commitment)
  # if metadata:
  #   try:
  #     client.set(cache_key, json.dumps(metadata), ex=(60 * 30))
  #   except Exception as e:
  #     pass
  metadata = get_nft_type(category=category, commitment=commitment)
  if metadata:
    try:
      client.set(cache_key, json.dumps(metadata), ex=(60 * 30))
    except Exception as e:
      pass

@shared_task(queue='resolve_metadata')
def update_tokencategorymetadata_cache(category, cache_key=None):
  client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
  cache_key = cache_key or f'tokencategorymetadata:{category}'
  # r = Registry.objects.filter(contents__identities__has_key=category)

  # if r.exists():
  #   r = r.latest('id')
  #   metadata = r.get_token_category_basic(category=category)
  #   if metadata:
  #     try:
  #       client.set(cache_key,json.dumps(metadata), ex=(60 * 30))
  #     except Exception as e:
  #       pass
  
  metadata = get_token_category_basic(category=category)
  if metadata:
    try:
      client.set(cache_key,json.dumps(metadata), ex=(60 * 30))
    except Exception as e:
      pass

