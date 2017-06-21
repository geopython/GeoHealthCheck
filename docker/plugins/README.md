# User Plugins

GHC User Plugins can add new Probes and Checks or extend existing ones.

## Via Docker

When using Docker, Plugins need to be available under `/GeoHealthCheck/GeoHealthCheck/plugins` within the 
GHC Docker Image or Container. 

You can choose to add your Plugins to the GHC Docker Image at build-time
or to the GHC Docker Container at run-time. The latter method is preferred as you can use the standard 
GHC Docker Image from Docker Hub. In both cases your
Plugin-modules and classes need to be configured in the GHC `GHC_USER_PLUGINS` Environment variable. 
                   
## At Image build-time

The following steps:

- place your Plugins within the sub-directory `user`
- do regular Docker build `docker build -t geopython/geohealthcheck .`

During the build Docker will `ADD` (copy) this dir to `/plugins` within the GHC Docker Image.
The [install.sh](../install.sh) script will then move `/plugins`
to the app-dir `/GeoHealthCheck/GeoHealthCheck/plugins`.
 
## At Container run-time (preferred)

The following steps:

- place your Plugins within this directory (or any other dir on your host)
- make a Docker Volume mapping from this dir to the Container internal dir `/plugins`
- specify your Plugins via Container Environment as `GHC_USER_PLUGINS: (comma-separated string of modules and/or classes)`
- within `GHC_USER_PLUGINS` the Python package `GeoHealthCheck.plugins` is needed as prefix
 
Example via [docker-compose.yml](../compose/docker-compose.yml):

```
services:
  geohealthcheck:
    image: geopython/geohealthcheck:latest
    ports:
      - 8083:80
    # Override settings to enable email notifications
    environment:
       GHC_USER_PLUGINS: 'GeoHealthCheck.plugins.user.myplugins'
       .
       .
    volumes:
      - ghc_sqlitedb:/GeoHealthCheck/DB
      - Path on the host, relative to the Compose file
      - ./../plugins:/plugins:ro
```

Or if you run the Image via `docker run` :


```
docker run -d --name GeoHealthCheck -p 8083:80 \
         -v ghc_sqlitedb:/GeoHealthCheck/DB \
         -v ./plugins:/plugins:ro \
         -e 'GHC_USER_PLUGINS=GeoHealthCheck.plugins.user.myplugins'
         geopython/geohealthcheck:latest
```

When the Container starts it will copy all content under
`/plugins` to the internal dir `/GeoHealthCheck/GeoHealthCheck/plugins`. 

