# Docker Installation

## Requirements

Docker installed and daemon running.

## Build

docker build -t yjacolin/geohealthcheck .

## Run

docker run -d --name GeoHealthCheck -p 8083:80 -v ghc_db:/GeoHealthCheck/DB yjacolin/geohealthcheck

go to http://localhost:8083
