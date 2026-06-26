# GHC with Docker Compose

[Docker](https://www.docker.com/) is the fastest/recommended way to get GHC up and running.
[Docker Compose](https://docs.docker.com/compose/) is *a tool for defining and running multi-container Docker applications.*

Within this directory are *examples* for running GHC using Docker compose.
You should copy and adapt these for your own deployment.

## Running with SQLite DB
```shell
docker compose up -d
docker compose down --remove-orphans

```
## Running with PostGIS DB
```shell
docker compose -f docker-compose.postgis.yml up -d
docker compose -f docker-compose.postgis.yml down --remove-orphans

```
