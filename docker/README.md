# Docker Installation

## Requirements

Docker installed and daemon running. 
NB: The ``docker`` commands below may need to be prepended with ``sudo``, dependent on your login rights.

## Build

Go to the subdir ``docker/GeoHealthCheck``, where the [Dockerfile](GeoHealthCheck/Dockerfile) resides, and issue:

```
docker build -t yjacolin/geohealthcheck .
````

## Run

```
docker run -d --name GeoHealthCheck -p 8083:80 -v ghc_db:/GeoHealthCheck/DB yjacolin/geohealthcheck
```

go to http://localhost:8083
