# Docker installation

## Build

docker build -t yjacolin/geohealtcheck .

## Run

docker run -d --name GeoHealtCheck -p 8082:80 -v DB:/GeoHealthCheck/DB yjacolin/geohealthcheck 
