from django.db import models
from bcmr_main.models import Token
from bcmr_main.models import Registry

class CashToken(Token):
  
  @property
  def nft_type(self):
    if not self.capability:
      return None
    
    registry = Registry.find_registry_by_token_category(self.category)
    if registry and registry.get('registry_id'):
      registry_instance = Registry.objects.get(id=registry.get('registry_id'))

      metadata = None 
      try:
        metadata = registry_instance.get_nft_type(category=self.category, commitment=self.commitment)
      except Exception as e:
        pass
      return metadata
  
  @property
  def token_category(self):
    registry = Registry.find_registry_by_token_category(self.category)
    if registry and registry.get('registry_id'):
      registry_instance = Registry.objects.get(id=registry.get('registry_id'))
      metadata = None 
      try:
        metadata = registry_instance.get_token_category_basic(category=self.category)
      except Exception as e:
        pass
      return metadata
      
  class Meta:
    proxy = True