
import json
from typing import Dict
from jsonschema import validate

class BitcoinCashMetadataRegistry:
  def __init__(self, contents:Dict) -> None:
    self.contents = contents
    self.validate(contents)
    b = contents
    self._schema = b.get('schema')
    self.version = b.get('version')
    self.latestRevision = b.get('latestRevision')
    self.registryIdentity = b.get('registryIdentity')
    self.identities = b.get('identities')
    self.tags = b.get('tags')
    self.defaultChain = b.get('defaultChain')
    self.chains = b.get('chains')
    self.license = b.get('license')
    self.extensions = b.get('extensions')
    self.authchainIdentity = b.get('authchainIdentity')

  def get_identity_history_timestamp(self):
    list(self.identities[self.registryIdentity].keys())[-1]

  def get_identity_snapshot(self):
    # onchain registry 
    if self.registryIdentity and type(self.registryIdentity) == str:
      if self.identities:
        return self.identities.get(self.registryIdentity).get(self.get_identity_history_timestamp())

  def get_icon_uri(self):
    if self.get_identity_snapshot():
      return self.get_identity_snapshot().get('uris').get('icon')
    
  def get_token(self):
    if self.get_identity_snapshot():
      return self.get_identity_snapshot().get('token')
    
  def get_symbol(self):
    if self.get_token():
      return self.get_token().get('symbol')
  
  def validate(self):
    BitcoinCashMetadataRegistry.validate(self.contents)

  @staticmethod
  def validate(contents):
    with open('./bcmr-schema-v2.json', 'r') as bcmr_schema_file:
      bcmr_schema = json.load(bcmr_schema_file)
      validate(instance=contents, schema=bcmr_schema)
    