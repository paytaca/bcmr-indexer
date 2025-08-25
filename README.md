# BCMR Indexer

Bitcoin Cash Metadata Registry (BCMR) indexer and validator

## Deployment

Requirements:
1. Ubuntu 22.04.4
2. Docker version 24.0.7
3. docker-compose version 1.29.2
4. Latest version of BCHN with tx index, rpc, and zmq enabled

## API endpoints

### Token Endpoints
- `/api/tokens/<category-id>` --> will give specific token metadata for FTs and generic token info for NFTs
- `/api/tokens/<category-id>/<type_key>/` --> will give token metadata for NFT types
- `/api/tokens/<category-id>/icon-symbol` --> will give token icon and symbol information

### Registry Endpoints
- `/api/registries/<category-id>/latest/` --> will give the latest registry record for the given category ID
- `/api/registry/<category-id>/` --> will give the registry for the given category ID

### BCMR Endpoints
- `/api/bcmr/<category-id>/` --> will give BCMR contents for the given category ID
- `/api/bcmr/<category-id>/token/` --> will give BCMR token information
- `/api/bcmr/<category-id>/token/nfts/<commitment>/` --> will give BCMR token NFT information
- `/api/bcmr/<category-id>/uris/` --> will give BCMR URIs
- `/api/bcmr/<category-id>/uris/icon` --> will give BCMR icon URI
- `/api/bcmr/<category-id>/uris/published-url` --> will give BCMR published URL
- `/api/bcmr/<category-id>/reindex/` --> will trigger reindexing of token registry

### Authchain Endpoints
- `/api/authchain/<category-id>/head/` --> will give authchain head information

### Identity Snapshot Endpoints
- `/api/registry/<category-id>/identity-snapshot/` --> will give identity snapshot
- `/api/registry/<category-id>/identity-snapshot/token-category/` --> will give token category information
- `/api/registry/<category-id>/identity-snapshot/token-category/nfts/` --> will give NFT information
- `/api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/bytecode/` --> will parse NFT bytecode
- `/api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/types/` --> will give NFT types
- `/api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/types/<commitment>/` --> will give NFT types by commitment

### Cash Token Endpoints
- `/api/cashtokens/` --> will give all cash tokens
- `/api/cashtokens/<category-id>/` --> will give cash tokens by category
- `/api/cashtokens/<category-id>/<token_type>/` --> will give cash tokens by category and type
- `/api/cashtokens/<category-id>/<token_type>/<commitment>/` --> will give cash tokens by category, type, and commitment

### Status Endpoints
- `/api/status/latest-block/` --> will give the latest block height that has been indexed

## Running your own instance

1. Copy `.env_template` and rename the copy to `.env`
2. Update the variables that need to be changed in `.env`
3. Run `docker-compose build`
4. Run `docker-compose up`
5. Check if it is up and running at http://localhost:8000

## Public instance

A public instance is available at [bcmr.paytaca.com](https://bcmr.paytaca.com/). <br>
The homepage shows overview statistics about the indexer and the API docs
