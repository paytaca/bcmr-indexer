# BCMR Indexer

Bitcoin Cash Metadata Registry (BCMR) indexer and validator

## Deployment

Requirements:
1. Ubuntu 22.04.4
2. Docker version 24.0.7
3. docker-compose version 1.29.2
4. Latest version of BCHN with tx index, rpc, and zmq enabled

## API endpoints

- `/api/tokens/<category-id>` --> will give specific token metadata for FTs and generic token info for NFTs
- `/api/tokens/<category-id>/<commitment>/` --> will give token metadata for NFT types
- `/api/registries/<category-id>/latest/` --> will give the latest registry record for the given category ID
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
