# BCMR indexer

## Start 
To start indexer you need to do:
1. `cp .env_template .env_dev`
2. Change variables with your. POSTGRES_HOST and REDIS_HOST must be as it mentioned in .env_template file, if you will use docker.
3. Start docker compose with: `docker compose up --build -d`

## How to use it
For using you can send request on your localhost:8000 (the port is in docker-compose.yml):
- api/status/latest-block/
- api/tokens/{token}
- api/tokens/{token}/{type_key}
- api/registries/{token}/latest
- api/authchain/{token}/head

## Recommended hardware
2 CPU, 8 GB RAM, 300 GB and more as a disk, SSD recommended.