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

Go to the GHC source root dir, 
where the [Dockerfile](../Dockerfile) resides, and issue:

```
docker build -t geopython/geohealthcheck .
```

At this point you may override several files that are copied into the Docker image.
For example [run.sh](run.sh) which launches GHC using the robust `gunicorn` WSGI server.

## Run

```
docker run -d --name GeoHealthCheck -p 8083:80 -v ghc_sqlitedb:/GeoHealthCheck/DB geopython/geohealthcheck:latest
```

go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host).

NB this runs GHC standalone with a `SQLite` DB, but without the cron-jobs that perform the healthchecks.
You may schedule the cron-jobs using the local cron system with the 
[cron-jobs-hourly](cron-jobs-hourly.sh) and
[cron-jobs-daily](cron-jobs-daily.sh) Docker Entrypoints.

But the most optimal way to run GHC with cronjobs and optionally Postgres backend DB,
is to use [Docker Compose](https://docs.docker.com/compose), see below.

## Using docker-compose

This allows a complete Docker setup, including cron-jobs and optionally using 
Postgres/PostGIS as database (recommended).  
See the [Docker Compose Documentation](https://docs.docker.com/compose)
for more info.

*Note that the `docker-compose` YAML files below are meant as examples to be adapted to your*
*local deployment situation.* 

### Using sqlite DB (default)

Using the default [docker-compose.yml](compose/docker-compose.yml) will run GHC with a SQLite DB.
Cronjobs are scheduled using [Jobber Cron](https://github.com/blacklabelops/jobber-cron/) as
regular Unix `cron` does not play nice with Docker.

To run (`-d` allows running in background):

```
cd docker/compose
docker-compose -f docker-compose.yml up  [-d]

# go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host)

```
  
### Using PostGIS DB

The file [docker-compose.postgis.yml](compose/docker-compose.postgis.yml) 
extends/overrides the default [docker-compose.yml](compose/docker-compose.yml) to use Postgres with PostGIS
as database.

To run, specify both `.yml` files:


```
cd docker/compose
docker-compose -f docker-compose.yml -f docker-compose.postgis.yml up [-d]

# go to http://localhost:8083 (port 80 in GHC Container is mapped to 8083 on host)


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

NB you may want to remove the port mapping `5432:5432` for the `postgis` container (it is not 
required for GHC and may expose a security issue). 
It is then still possible to access your database, like via psql, by figuring out
the Docker host IP address on your Docker host as follows: 


```                                       
  export PGHOST=`sudo docker inspect --format '{{ .NetworkSettings.IPAddress }}' postgis`
  psql -U ghc ghc

```

## Cronjobs

Cronjobs via `docker-compose` are scheduled using [Jobber Cron](https://github.com/blacklabelops/jobber-cron/).
See this snippet from the  [docker-compose.yml](compose/docker-compose.yml):

```
jobber:
	image: blacklabelops/jobber:docker.v1.1
	depends_on:
	  - geohealthcheck-cron-hourly
	  - geohealthcheck-cron-daily
	environment:
	  # May see warnings, see https://github.com/blacklabelops/rsnapshot/issues/2 but ok.
	  JOB_NAME1: ghc-cron-hourly
	  JOB_COMMAND1: docker start $$(docker ps -a -f label=io.ghc-cron-hourly=true --format="{{.ID}}")
	  JOB_TIME1: 0 0 *
	  JOB_NAME2: ghc-cron-daily
	  JOB_COMMAND2: docker start $$(docker ps -a -f label=io.ghc-cron-daily=true --format="{{.ID}}")
	  JOB_TIME2: 0 45 0 *
	volumes:
	  - /var/run/docker.sock:/var/run/docker.sock

```

This configures two jobs `geohealthcheck-cron-hourly` (every whole hour) and
`geohealthcheck-cron-daily` (every night at 00:45). Both run the GHC Docker image with different
containers and entrypoints. You may want to setup additional jobs e.g. to backup the database.
For example the daily cron-job entry looks like:

```
geohealthcheck-cron-daily:
	image: geopython/geohealthcheck:latest
	depends_on:
	  - geohealthcheck
	entrypoint:
	  - bash
	  - /cron-jobs-daily.sh
	volumes:
	  - ghc_sqlitedb:/GeoHealthCheck/DB
	labels:
	  io.ghc-cron-daily: 'true'
```

NB: the Jobber entries are run when docker-compose runs, there may be an error when the DB
is not yet setup in the main GHC Docker Container, you can ignore this.

NB you may see these Jobber warnings:

```
Failed to load jobs for open /dev/null/.jobber: not a directory: sshd
Failed to load jobs for open /dev/null/.jobber: not a directory: guest

```

These are not errors, see [this Jobber issue](https://github.com/blacklabelops/rsnapshot/issues/2).
Make sure your jobs are scheduled, via:


```
# Enter the container:
$ docker exec -it compose_jobber_1 bash
# List Jobber Jobs:
$ jobber list

NAME             STATUS  SEC/MIN/HR/MDAY/MTH/WDAY  NEXT RUN TIME         NOTIFY ON ERR  NOTIFY ON FAIL  ERR HANDLER
ghc-cron-hourly  Good    0 0 * * * *               Jul  9 14:00:00 2017  false          false           Continue
ghc-cron-daily   Good    0 45 0 * * *              Jul 10 00:45:00 2017  false          false           Continue

# Test job execution:
$ jobber test ghc-cron-hourly
$ jobber test ghc-cron-daily

```

## Configuration

The default GHC configuration is specified within the [Dockerfile](../Dockerfile).
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

