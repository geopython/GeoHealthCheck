# User Plugins

GHC User Plugins can add new Probes and Checks or extend existing ones.

## In Regular GHC App

There's always two steps required to get your Plugins available in the GHC
App:

- add their class or module names to available Plugins config in your `site_config.py`
- add their location to the `PYTHONPATH`

Easiest is to directly add your Plugins in the directory  `GeoHealthCheck/plugins/user` under
your GHC install dir. In that case step 2 is not required, but you should name the Plugins
`GeoHealthCheck.plugins.user.<yourmodule>.[yourclass]` within  `site_config.py` 
such that they can be found in the app's `PYTHONPATH`.

## Via Docker

When using Docker, Plugins need to be available under `/userplugins` within the 
GHC Docker Image or Container. When the Container starts it will copy all content under
`/userplugins` to the internal dir `/GeoHealthCheck/GeoHealthCheck/plugins/user`. 
                   
Plugins can be added to your app as follows:

- add to Docker Image at build-time
- add to Docker Container at run-time, e.g. via Docker Compose

See  [Docker Readme at GHC GitHub](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md)
for more info.
