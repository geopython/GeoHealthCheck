FROM python:2.7.13-alpine

# Thanks to http://www.sandtable.com/reduce-docker-image-sizes-using-alpine
# FROM debian:jessie

# Credits to yjacolin for providing first versions
LABEL original_developer="yjacolin <yves.jacolin@camptocamp.com>" \
	maintainer="Just van den Broecke <justb4@gmail.com>"

# These are default values,
# Override when running container via docker(-compose)

# General ENV settings
ENV LC_ALL="en_US.UTF-8" \
	LANG="en_US.UTF-8" \
	LANGUAGE="en_US.UTF-8" \
    \
	\
	# GHC ENV settings\
	ADMIN_NAME=admin \
	ADMIN_PWD=admin \
	ADMIN_EMAIL=admin.istrator@mydomain.com \
	SQLALCHEMY_DATABASE_URI='sqlite:////GeoHealthCheck/DB/data.db' \
	SECRET_KEY='d544ccc37dc3ad214c09b1b7faaa64c60351d5c8bb48b342' \
	GHC_PROBE_HTTP_TIMEOUT_SECS=30 \
	GHC_RETENTION_DAYS=30 \
	GHC_SELF_REGISTER=False \
	GHC_NOTIFICATIONS=False \
	GHC_NOTIFICATIONS_VERBOSITY=True \
	GHC_WWW_LINK_EXCEPTION_CHECK=False \
	GHC_ADMIN_EMAIL='you@example.com' \
	GHC_RUNNER_IN_WEBAPP=False \
	GHC_LOG_LEVEL=30 \
	GHC_LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s' \
	GHC_NOTIFICATIONS_EMAIL='you2@example.com,them@example.com' \
	GHC_SITE_TITLE='GeoHealthCheck' \
	GHC_SITE_URL='http://localhost' \
	GHC_SMTP_SERVER=None \
	GHC_SMTP_PORT=None \
	GHC_SMTP_TLS=False \
	GHC_SMTP_SSL=False \
	GHC_SMTP_USERNAME=None \
	GHC_SMTP_PASSWORD=None \
	GHC_METADATA_CACHE_SECS=900 \
    \
# WSGI server settings, assumed is gunicorn  \
HOST=0.0.0.0 \
PORT=80 \
WSGI_WORKERS=4 \
WSGI_WORKER_TIMEOUT=6000 \
WSGI_WORKER_CLASS='eventlet' \
\
# GHC Core Plugins modules and/or classes, seldom needed to set:  \
# if not specified here or in Container environment  \
# all GHC built-in Plugins will be active.  \
#ENV GHC_PLUGINS 'GeoHealthCheck.plugins.probe.owsgetcaps,\
#        GeoHealthCheck.plugins.probe.wms, ...., ...\
#        GeoHealthCheck.plugins.check.checks' \
\
# GHC User Plugins, best be overridden via Container environment \
GHC_USER_PLUGINS=''

RUN apk add --no-cache --virtual .build-deps gcc build-base linux-headers postgresql-dev \
    && apk add --no-cache bash postgresql-client tzdata openntpd \
    && pip install virtualenv \
    && rm -rf /var/cache/apk/* /tmp/* /var/tmp/*

# Add standard files and Add/override Plugins
# Alternative Entrypoints to run GHC jobs
# Override default Entrypoint with these on Containers
ADD docker/scripts/*.sh docker/config_site.py docker/plugins /

# Add Source Code
ADD . /GeoHealthCheck

# Install and Remove build-related packages for smaller image size
RUN chmod a+x /*.sh && bash install.sh && apk del .build-deps

# For SQLite
VOLUME ["/GeoHealthCheck/DB/"]

EXPOSE ${PORT}

ENTRYPOINT /run-web.sh
