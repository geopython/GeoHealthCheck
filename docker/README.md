# Running GHC with Docker

## Requirements

Docker installed and daemon running. 
NB: The ``docker`` commands below may need to be prepended with ``sudo``, dependent on your login rights.

Note: `yjacolin/geohealthcheck` will become `geopython/geohealthcheck` available from Docker Hub very soon!

## Build

Go to the subdir ``docker/GeoHealthCheck``, 
where the [Dockerfile](GeoHealthCheck/Dockerfile) resides, and issue:

```
docker build -t yjacolin/geohealthcheck .
````

## Run

```
docker run -d --name GeoHealthCheck -p 8083:80 -v ghc_sqlitedb:/GeoHealthCheck/DB yjacolin/geohealthcheck
```

go to http://localhost:8083

## Using docker-compose

This allows a complete Docker setup, including cron-jobs and optionally using 
Postgres/PostGIS as database (recommended).  See the [Docker Compose Documentation](https://docs.docker.com/compose)
for more info.

### Using sqlite DB (default)

Using the default [docker-compose.yml](docker-compose.yml) will run GHC with a SQLite DB.
Cronjobs are scheduled using [Jobber Cron](https://github.com/blacklabelops/jobber-cron/) as
regular Unix `cron` does not play nice with Docker.

To run (`-d` allows running in background):

```
docker-compose -f docker-compose.yml up  [-d]

```
  
### Using PostGIS DB

The file [docker-compose.postgis.yml](docker-compose.postgis.yml) 
extends/overrides the default [docker-compose.yml](docker-compose.yml) to use Postgres with PostGIS
as database.

To run, specify both `.yml` files:


```
docker-compose -f docker-compose.yml -f docker-compose.postgis.yml up [-d]

```

On the first run, the PG container will create an empty DB. The GHC container will
wait until PG is ready and if DB is empty populate the DB with GHC tables. NB you
may see errors on first run from the cron-jobs. These are always immediately run at startup
while the GHC container is still waiting for the DB to be ready.

To access your Postgres DB while running:

```

# Bash into running GHC Container
docker exec -it docker_geohealthcheck_1 bash

# In GHC Container access DB with psql using DB parms
psql -h postgis_ghc -U ghc ghc

```

The PG DB data is kept in a Docker volume usually located at  
`/var/lib/docker/volumes/docker_ghc_pgdb/_data`. 
 
## Other tasks

You can always `bash` into the GHC container to run maintenance tasks.
The GHC installation is at `/GeoHealthCheck`.

```

# Bash into running GHC Container
docker exec -it docker_geohealthcheck_1 bash

# setup Python venv
source /venv/bin/activate .
cd /GeoHealthCheck/
 
# next can use Paver commands e.g. DB upgrade
paver upgrade

etc
```

