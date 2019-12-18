# GHC with Docker

[Docker](https://www.docker.com/) is the fastest/recommended way to get GHC up and running. 
GHC Docker images are hosted at [Docker Hub](https://hub.docker.com/r/geopython/geohealthcheck) 
In the best case an install/run of GHC is a matter of minutes!

If you are reading this from Docker Hub, local links will not work. 
In that case use the [Docker Readme at GHC GitHub](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md).

Since GHC release 0.4.0 GHC can run completely with two Docker containers from the same
GHC Docker image:

* `GHC Webapp` the web/Flask app
* `GHC Runner` : the daemon runner app that schedules and executes GHC's Probes

## Requirements

Docker installed and Docker daemon running.
[Docker Compose](https://docs.docker.com/compose/install) is separate install.

For installing Docker on Ubuntu there
is a  [bash helper script](install-docker-ubuntu.sh).

NB: The ``docker`` commands below may need to be prepended with 
``sudo``, dependent on your login rights.

## Build

This step is not necessary as GHC Docker images are available 
from [Docker Hub](https://hub.docker.com/r/geopython/geohealthcheck).
Only in cases where you have local changes, this step is required.

Go to the GHC source root dir, 
where the [Dockerfile](../Dockerfile) resides, and issue:

```
docker build -t geopython/geohealthcheck .
```

At this point you may override several files that are copied into the Docker image.
For example [run.sh](run.sh) which launches GHC using the robust `gunicorn` WSGI server.

## Run

```
docker run -d --name ghc_web -p 8083:80 -v ghc_sqlitedb:/GeoHealthCheck/DB geopython/geohealthcheck:latest
```

go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host).

NB this runs GHC standalone with a `SQLite` DB and with the GHC Runner that performs the
healthchecks. But this may in cases not be optimal as the `GHC Webapp`  may get overloaded 
from processing by the `GHC Runner`. Tip: to see detailed logging add `-e GHC_LOG_LEVEL=10 `.

This mode can be disabled by passing `GHC_RUNNER_IN_WEBAPP` to as an ENV 
var to the Docker container:

```
docker run  --name ghc_web -e GHC_RUNNER_IN_WEBAPP=False -p 8083:80 -v ghc_sqlitedb:/GeoHealthCheck/DB geopython/geohealthcheck:latest

```

This allows both the `GHC Webapp` (Dashboard)and `GHC Runner` within a separate Docker containers.

You can then run `GHC Runner` as a separate container by overriding
the default `ENTRYPOINT` with `/run-runner.sh`:

```
docker run -d --name ghc_runner --entrypoint "/run-runner.sh" -v ghc_sqlitedb:/GeoHealthCheck/DB geopython/geohealthcheck:latest
```

But the most optimal way to run GHC with scheduled jobs and optionally Postgres as backend DB,
is to use [Docker Compose](https://docs.docker.com/compose), see below.

## Using docker-compose

This allows a complete Docker setup, including scheduling and optionally using 
Postgres/PostGIS as database (recommended).  
See the [Docker Compose Documentation](https://docs.docker.com/compose)
for more info. GHC Webapp and Runner are in this case 
deployed as separate processes (Docker containers).

*Note that the `docker-compose` YAML files below are meant as examples to be adapted to your*
*local deployment situation.* 

### Using sqlite DB (default)

Using the default [docker-compose.yml](compose/docker-compose.yml) will run GHC with a SQLite DB.


To run (`-d` allows running in background):

```
cd docker/compose
docker-compose -f docker-compose.yml up  [-d]

# go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host)

```
  
### Using PostGIS DB

The file [docker-compose.postgis.yml](compose/docker-compose.postgis.yml)  is
similar but uses Postgres as the database.

To run:


```
cd docker/compose
docker-compose -f docker-compose.postgis.yml up [-d]

# go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host)


```

On the first run, the PG container will create an empty DB. The GHC container will
wait until PG is ready and if DB is empty populate the DB with GHC tables. NB you
may see errors on first run from the cron-jobs. These are always immediately run at startup
while the GHC container is still waiting for the DB to be ready.

To access your Postgres DB while running:

```

# Bash into running GHC Container
docker exec -it ghc_web bash

# In GHC Container access DB with psql using DB parms
psql -h postgis_ghc -U ghc ghc

```

The PG DB data is kept in a Docker volume usually located at  
`/var/lib/docker/volumes/docker_ghc_pgdb/_data`. 

NB you may want to remove the port mapping `5432:5432` for the `postgis` container (it is not 
required for GHC and may expose a security issue). 
It is then still possible to access your database, like via psql, by figuring out
the Docker host IP address on your Docker host as follows: 


```                                       
  export PGHOST=`sudo docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgis`
  psql -U ghc ghc

```

## Cron jobs

DEPRECATED: Cronjobs via `docker-compose` are since v0.4.0 no longer scheduled via Jobber (cron) 
but within GHC itself. The GHC Docker Image can run as a Container in a daemon runner
role that executes all GHC scheduled runs from the DB directly.
But with the per-Resource scheduling introduced in v0.4.0, cron-jobs
cannot support the detailed scheduling required.


## Configuration

The default GHC configuration is specified within the [Dockerfile](../Dockerfile).
This allows overriding these `ENV` vars during deployment (as opposed to having to build
your own GHC Docker Image). Docker (`-e` options) and Docker Compose (`environment` and/or `env_file` 
sections) allow setting Environment variables.  

Here we use `.env` files.

```
  ghc_runner:
    image: geopython/geohealthcheck:latest

    container_name: ghc_runner

    env_file:
      - ghc.env

    entrypoint:
      - /run-runner.sh

    volumes:
      - ghc_sqlitedb:/GeoHealthCheck/DB

```

This applies variables specified in [ghc.env](compose/ghc.env) to the Docker container.

One may override these with another file as is done in the Postgres
version:

```
  ghc_runner:
    image: geopython/geohealthcheck:latest

    container_name: ghc_runner

    env_file:
      - ghc.env
      - ghc-postgis.env

    links:
      - postgis_ghc

    depends_on:
      - postgis_ghc

    entrypoint:
      - /run-runner.sh

  postgis_ghc:
    image: mdillon/postgis:9.6-alpine

    container_name: postgis_ghc

    env_file:
      - ghc-postgis.env

    volumes:
      - ghc_pgdb:/var/lib/postgresql/data

```

Here [ghc-postgis.env](compose/ghc-postgis.env) adds extra Postgres-related config settings.

## Other tasks

You can always `bash` into the GHC Container to run maintenance tasks.
The GHC installation is at `/GeoHealthCheck` within the Docker Container.

```

# Bash into running GHC Container
docker exec -it docker_geohealthcheck_1 bash

# setup Python venv
source /venv/bin/activate .
cd /GeoHealthCheck/
 
# next can use cli commands e.g. DB upgrade
geohc db-upgrade

etc
```

NB: database upgrades (`paver upgrade`)
are always performed automatically when running GHC via Docker.
