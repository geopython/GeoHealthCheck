# Docker installation

## Build

docker build -t yjacolin/geohealthcheck .

## Run

docker run -d --name GeoHealtCheck -p 8083:80 -v ghc_db:/GeoHealthCheck/DB yjacolin/geohealthcheck 
