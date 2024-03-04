import redis
import json
from django.db import models
from bcmr_main.models import Token
from bcmr_main.models import Registry
from decouple import config
from .tasks import update_nftmetadata_cache

class CashToken(Token):
  
  @property
  def nft_type(self):
    if not self.capability:
      return None
    client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
    cache_key = f'nftmetadata:{self.category}:{self.commitment}'  
    metadata = client.get(cache_key)
    
    if metadata:
      update_nftmetadata_cache.delay(self.category, self.commitment, cache_key)
      return json.loads(metadata)
    
    r = Registry.objects.filter(contents__identities__has_key=self.category)

    if r.exists():
      r = r.latest('id')
      metadata = r.get_nft_type(category=self.category, commitment=self.commitment)
    if metadata:
      try:
        client.set(cache_key, json.dumps(metadata), ex=(60 * 30))
      except Exception as e:
        pass
    
    return metadata
  
  @property
  def token_category(self):

    client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))
    metadata = client.get(f'{self.category}_token-category')

    if metadata:
      metadata = json.loads(metadata)
      return metadata

    registry_id = client.get(f'{self.category}_registry-id')

    if registry_id:
      registry_id = int(registry_id.decode())
    else:
      registry = Registry.find_registry_id(self.category)
      if registry and registry.get('registry_id'):
        registry_id = registry.get('registry_id')
        client.set(f'{self.category}_registry-id', registry_id, ex=(60 * 30))

    if registry_id:
      registry_instance = Registry.objects.get(id=registry_id)
      metadata = None 
      try:
        metadata = registry_instance.get_token_category_basic(category=self.category)
        if metadata:
          client.set(f'{self.category}_token-category',json.dumps(metadata), ex=(60 * 30))
      except Exception as e:
        pass
      return metadata
      
  class Meta:
    proxy = True