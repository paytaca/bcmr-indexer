import redis
import json
from django.db import models
from bcmr_main.models import Token
from bcmr_main.models import Registry
from decouple import config
from .tasks import update_nftmetadata_cache, update_tokencategorymetadata_cache

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
    cache_key = f'tokencategorymetadata:{self.category}'
    metadata = client.get(cache_key)
    
    if metadata:
      metadata = json.loads(metadata)
      update_tokencategorymetadata_cache.delay(self.category, self.commitment, cache_key)
      return metadata

    r = Registry.objects.filter(contents__identities__has_key=self.category)

    if r.exists():
      r = r.latest('id')
      if r:
        try:
          metadata = r.get_token_category_basic(category=self.category)
          if metadata:
            client.set(cache_key,json.dumps(metadata), ex=(60 * 30))
        except Exception as e:
          pass

    return metadata
      
  class Meta:
    proxy = True