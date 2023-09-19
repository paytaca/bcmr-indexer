
import json
from typing import Dict
from jsonschema import validate

class BitcoinCashMetadataRegistry:
  def __init__(self, contents:Dict) -> None:
    self.contents = contents
    self._schema = contents.get('schema')
    self.version = contents.get('version')
    self.latestRevision = contents.get('latestRevision')
    self.registryIdentity = contents.get('registryIdentity')
    self.identities = contents.get('identities')
    self.tags = contents.get('tags')
    self.defaultChain = contents.get('defaultChain')
    self.chains = contents.get('chains')
    self.license = contents.get('license')
    self.extensions = contents.get('extensions')
    self.authchainIdentity = contents.get('authchainIdentity')

  def get_identity_history_timestamp(self):
    return list(self.identities[self.registryIdentity].keys())[-1]

  def get_identity_snapshot(self):
    # onchain registry 
    if self.registryIdentity and type(self.registryIdentity) == str:
      if self.identities:
        return self.identities.get(self.registryIdentity).get(self.get_identity_history_timestamp())

  def get_uris(self):
    if self.get_identity_snapshot():
      return self.get_identity_snapshot().get('uris')

  def get_icon_uri(self):
    try:
      return self.get_uris().get('icon')
    except AttributeError:
      pass

    
    
  def get_token(self):
    if self.get_identity_snapshot():
      return self.get_identity_snapshot().get('token')
    
  def get_symbol(self):
    if self.get_token():
      return self.get_token().get('symbol')
    
  def get_nft(self, commitment):
    try:
      return self.get_token().get('nfts').get('types').get(commitment)
    except AttributeError:
      pass

  def validate(self):
    BitcoinCashMetadataRegistry.validate_contents(self.contents)

  @staticmethod
  def validate_contents(contents):
    with open('./bcmr-schema-v2.json', 'r') as bcmr_schema_file:
      bcmr_schema = json.load(bcmr_schema_file)
      validate(instance=contents, schema=bcmr_schema)
    