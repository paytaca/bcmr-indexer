import redis
import json
from django.db import models
from bcmr_main.models import Token
from bcmr_main.models import Registry
from decouple import config


class CashToken(Token):
  
  @property
  def nft_type(self):
    if not self.capability:
      return None
    
    client = redis.Redis(host=config('REDIS_HOST', 'redis'), port=config('REDIS_PORT', 6379))

    metadata = client.get(f'{self.category}_{self.commitment}_nft-type')

    if metadata:
      metadata = json.loads(metadata)
      return metadata
    
    registry_id = client.get(f'{self.category}_registry-id')

    if registry_id:
      registry_id = int(registry_id.decode())
    else:
      registry = Registry.find_registry_by_token_category(self.category)
      if registry and registry.get('registry_id'):
        registry_id = registry.get('registry_id')
        client.set(f'{self.category}_registry-id', registry_id, ex=(60 * 30))
        
    if registry_id:

      registry_instance = Registry.objects.get(id=registry_id)

      metadata = None 
      try:
        metadata = registry_instance.get_nft_type(category=self.category, commitment=self.commitment)
        if metadata:
          client.set(f'{self.category}_{self.commitment}_nft-type',json.dumps(metadata), ex=(60 * 30))
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
      registry = Registry.find_registry_by_token_category(self.category)
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