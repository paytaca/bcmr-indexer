# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-31
Initial public release of the **BCMR Indexer**: a Django-based indexer + API for Bitcoin Cash Metadata Registry (BCMR) data and CashTokens registry/identity snapshots.

### Added
- **On-chain ingestion**
  - Block scanner management command to index transactions from the CashTokens activation height (network-aware).
  - ZMQ mempool listener management command to process unconfirmed transactions in near real-time.
- **BCMR + registry processing**
  - Parsing of BCMR OP_RETURN payloads during transaction processing.
  - Authbase / identity-output tracking used to build token authchains and associate registries with token categories.
  - Background tasks to resolve/generate token metadata from registry contents.
  - Periodic task to re-check and backfill missing block/time fields for unconfirmed transactions once confirmed.
- **HTTP API (Django REST Framework)**
  - Token metadata endpoints:
    - `GET /api/tokens/<category-id>/`
    - `GET /api/tokens/<category-id>/<type_key>/`
    - `GET /api/tokens/<category-id>/icon-symbol`
  - Registry endpoints:
    - `GET /api/registries/<category-id>/latest/`
    - `GET /api/registries/<txid>:<vout>/` (TXO-based registry lookup)
  - BCMR convenience endpoints:
    - `GET /api/bcmr/<category-id>/`
    - `GET /api/bcmr/<category-id>/token/`
    - `GET /api/bcmr/<category-id>/token/nfts/<commitment>/`
    - `GET /api/bcmr/<category-id>/uris/`
    - `GET /api/bcmr/<category-id>/uris/icon`
    - `GET /api/bcmr/<category-id>/uris/published-url`
    - `POST /api/bcmr/<category-id>/reindex/` (trigger reindexing)
  - Authchain endpoint:
    - `GET /api/authchain/<category-id>/head/`
  - Identity snapshot + CashTokens endpoints:
    - `GET /api/registry/<category-id>/identity-snapshot/`
    - `GET /api/registry/<category-id>/identity-snapshot/token-category/`
    - `GET /api/registry/<category-id>/identity-snapshot/token-category/nfts/`
    - `GET /api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/bytecode/`
    - `GET /api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/types/`
    - `GET /api/registry/<category-id>/identity-snapshot/token-category/nfts/parse/types/<commitment>/`
    - `GET /api/cashtokens/`
    - `GET /api/cashtokens/<category-id>/`
    - `GET /api/cashtokens/<category-id>/<token_type>/`
    - `GET /api/cashtokens/<category-id>/<token_type>/<commitment>/`
  - Status endpoint:
    - `GET /api/status/latest-block/`
- **Caching + operations**
  - Redis-backed caching for registry/token metadata responses, including utilities to clear caches by token category.
  - Docker Compose stack for local deployment (Django backend + Postgres + Redis).

[0.1.0]: https://github.com/paytaca/bcmr-indexer/releases/tag/v0.1.0
