# GHC with Docker

[Docker](https://www.docker.com/) is the fastest/recommended way to get GHC up and running. 
GHC Docker images are hosted at [Docker Hub](https://hub.docker.com/r/geopython/geohealthcheck) 
In the best case an install/run of GHC is a matter of minutes!

If you are reading this from Docker Hub, local links will not work. 
In that case use the [Docker Readme at GHC GitHub](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md).

## Requirements

Docker installed and Docker daemon running.
[Docker Compose](https://docs.docker.com/compose/install) is separate install.

For installing Docker on Ubuntu there
is a  [bash helper script](install-docker-ubuntu.sh).

NB: The ``docker`` commands below may need to be prepended with ``sudo``, dependent on your login rights.

## Build

This step is not necessary as GHC Docker images are available 
from [Docker Hub](https://hub.docker.com/r/geopython/geohealthcheck).
Only in cases where you have local changes, this step is required.

Go to the subdir ``docker/GeoHealthCheck``, 
where the [Dockerfile](GeoHealthCheck/Dockerfile) resides, and issue:

```
docker build -t geopython/geohealthcheck .
```

### Build Arguments

These are the build args with defaults:

```
ARG GHC_GIT_REPO="https://github.com/geopython/GeoHealthCheck.git"
ARG GHC_GIT_BRANCH="master"
```

So with no args the GHC master branch is built. You can build from a
specific GitHub repo and/or branch, e.g.

```
sudo docker build --build-arg GHC_GIT_BRANCH=dev -t geopython/geohealthcheck:dev .
```

This is mainly for development purposes.

## Run

```
docker run -d --name GeoHealthCheck -p 8083:80 -v ghc_sqlitedb:/GeoHealthCheck/DB geopython/geohealthcheck:latest
```

go to http://localhost:8083.

NB this runs GHC standalone with a `SQLite` DB, but without the cron-jobs that perform the healthchecks.
You may schedule the cron-jobs using the local cron system with the 
[cron-jobs-hourly](GeoHealthCheck/cron-jobs-hourly.sh) and
[cron-jobs-daily](GeoHealthCheck/cron-jobs-daily.sh) Docker Entrypoints.

But the most optimal way to run GHC with cronjobs and optionally Postgres backend DB,
is to use [Docker Compose](https://docs.docker.com/compose), see below.

## Using docker-compose

This allows a complete Docker setup, including cron-jobs and optionally using 
Postgres/PostGIS as database (recommended).  
See the [Docker Compose Documentation](https://docs.docker.com/compose)
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
 
## Configuration

The default GHC configuration is specified within the [Dockerfile](GeoHealthCheck/Dockerfile).
This allows overriding these `ENV` vars during deployment (as opposed to having to build
your own GHC Docker Image). Docker (`-e` options) and Docker Compose (`environment` section)
allow setting Environment variables.  

For example, to enable sending email notifications
in Dutch witin the GHC hourly job, specify the `environment` like:

```
   geohealthcheck-cron-hourly:
     image: geopython/geohealthcheck:latest
     depends_on:
       - geohealthcheck
 
     # Override settings to enable email notifications
     environment:
       LC_ALL: "nl_NL.UTF-8"
       LANG: "nl_NL.UTF-8"
       LANGUAGE: "nl_NL.UTF-8"
       GHC_NOTIFICATIONS: 'true'
       GHC_NOTIFICATIONS_VERBOSITY: 'true'
       GHC_ADMIN_EMAIL: 'us@gmail.com'
       GHC_NOTIFICATIONS_EMAIL: 'us@gmail.com,them@domain.com'
       GHC_SMTP_SERVER: 'smtp.gmail.com'
       GHC_SMTP_PORT: 587
       GHC_SMTP_TLS: 'true'
       GHC_SMTP_SSL: 'false'
       GHC_SMTP_USERNAME: 'us@gmail.com'
       GHC_SMTP_PASSWORD: 'the_passw'
       GHC_USER_PLUGINS: 'GeoHealthCheck.plugins.user.myplugins'
       .
       .

```

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

