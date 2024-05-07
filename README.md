# BCMR Indexer

Bitcoin Cash Metadata Registry (BCMR) indexer and validator

## API endpoints

- `/api/tokens/<category-id>` --> will give specific token metadata for FTs and generic token info for NFTs
- `/api/tokens/<category-id>/<commitment>/` --> will give token metadata for NFT types
- `/api/registries/<category-id>/latest/` --> will give the latest registry record for the given category ID

## Public instance

A public API is available at [bcmr.paytaca.com](https://bcmr.paytaca.com/). <br>
The homepage shows overview statistics about the indexer.
