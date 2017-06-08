FROM python:2.7.13-alpine

# Thanks to http://www.sandtable.com/reduce-docker-image-sizes-using-alpine
# FROM debian:jessie

# Credits to yjacolin for providing first versions
LABEL original_developer "yjacolin <yves.jacolin@camptocamp.com>"
LABEL maintainer "Just van den Broecke <justb4@gmail.com>"

# May specify any GHC Git Repo/branch as build arg, default is master
# e.g. https://github.com/geopython/GeoHealthCheck.git
ARG GHC_GIT_REPO="https://github.com/geopython/GeoHealthCheck.git"
ARG GHC_GIT_BRANCH="master"
# These are default values,
# Override when running container via docker(-compose)

# General ENV settings
ENV LC_ALL "en_US.UTF-8"
ENV LANG "en_US.UTF-8"
ENV LANGUAGE "en_US.UTF-8"

# GHC ENV settings
ENV ADMIN_NAME admin
ENV ADMIN_PWD admin
ENV ADMIN_EMAIL admin.istrator@mydomain.com
ENV SQLALCHEMY_DATABASE_URI 'sqlite:////GeoHealthCheck/DB/data.db'
ENV HOST 0.0.0.0
ENV PORT 80
ENV SECRET_KEY 'd544ccc37dc3ad214c09b1b7faaa64c60351d5c8bb48b342'
ENV GHC_RETENTION_DAYS 30
ENV GHC_RUN_FREQUENCY 'hourly'
ENV GHC_SELF_REGISTER False
ENV GHC_NOTIFICATIONS False
ENV GHC_NOTIFICATIONS_VERBOSITY True
ENV GHC_WWW_LINK_EXCEPTION_CHECK False
ENV GHC_ADMIN_EMAIL 'you@example.com'
ENV GHC_NOTIFICATIONS_EMAIL 'you2@example.com,them@example.com'
ENV GHC_SITE_TITLE 'GeoHealthCheck'
ENV GHC_SITE_URL 'http://localhost'
ENV GHC_SMTP_SERVER None
ENV GHC_SMTP_PORT None
ENV GHC_SMTP_TLS False
ENV GHC_SMTP_SSL False
ENV GHC_SMTP_USERNAME None
ENV GHC_SMTP_PASSWORD None

# GHC Core Plugins modules annd/or classes, seldom needed to set:
# if not specified here or in Container environment
# all GHC built-in Plugins will be active.
#ENV GHC_PLUGINS 'GeoHealthCheck.plugins.probe.owsgetcaps,\
#        GeoHealthCheck.plugins.probe.wms, ...., ...\
#        GeoHealthCheck.plugins.check.checks'

# GHC User Plugins, best be overridden via Container environment
ENV GHC_USER_PLUGINS ''

RUN apk add --no-cache --virtual .build-deps git gcc build-base linux-headers postgresql-dev \
    && apk add --no-cache bash vim postgresql-client \
    && pip install virtualenv \
    && rm -rf /var/cache/apk/* /tmp/* /var/tmp/*

# Old: for debian:jessie, now using alpine linux
#RUN apt-get update && \
#    apt-get install -qqy virtualenv git python-pip python-dev vim libpq-dev postgresql-client && \
#    apt-get autoremove -y ; apt-get clean ; \
#    rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

# Add standard files and Add/override Plugins
# Alternative Entrypoints to run GHC jobs
# Override default Entrypoint with these on Containers
ADD install.sh entrypoint.sh config_site.py cron-jobs-daily.sh cron-jobs-hourly.sh plugins /  
RUN	chmod a+x /cron-jobs-*.sh

# Add Source Code TODO (need to move Dockerfile to root dir)
# ADD . /GeoHealthCheck

# Install and Remove build-related packages for smaller image size
RUN bash install.sh  \
	&& apk del .build-deps

# For SQLite
VOLUME ["/GeoHealthCheck/DB/"]

EXPOSE ${PORT}

ENTRYPOINT /entrypoint.sh
