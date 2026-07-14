FROM ghcr.io/prefix-dev/pixi:0.72.2-noble AS build

# ARGS
ARG LANGUAGE="en_US"
ARG ENCODING="UTF-8"

ENV LOCALE_STR="${LANGUAGE}.${ENCODING} ${ENCODING}" \
    DEBIAN_FRONTEND=noninteractive

# Install and Configure default locale
# NB GHC has its own language handlling via Babel.
RUN apt update -y \
    && apt install -y locales \
    && echo "${LOCALE_STR}" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pixi install -e prod --locked
RUN echo '#!/bin/bash' > /app/pixi-env.sh
RUN pixi shell-hook -e prod -s bash --as-is >> /app/pixi-env.sh
RUN echo 'exec "$@"' >> /app/pixi-env.sh
RUN echo chmod +x /app/pixi-env.sh
RUN pixi run -e prod setup
RUN cp docker/config_site.py instance/
RUN if [ -d  docker/plugins ]; then cp -ar docker/plugins/* /app/GeoHealthCheck/plugins/; fi

# Slim down, removing unused files generated within build
RUN rm -rf /app/GeoHealthCheck/docs
RUN find /app/GeoHealthCheck/static/lib -type d -name docs | xargs rm -rf
RUN find /app/GeoHealthCheck/static/lib -type d -name src | xargs rm -rf

FROM ubuntu:24.04 AS production

# Credits to yjacolin for providing first versions
LABEL original_developer="yjacolin <yves.jacolin@camptocamp.com>" \
	maintainer="Just van den Broecke <justb4@gmail.com>"

# Copy the compiled locale files from the builder
COPY --from=build /usr/lib/locale/locale-archive /usr/lib/locale/locale-archive
COPY --from=build /etc/locale.gen /etc/locale.gen
COPY --from=build /etc/default/locale /etc/default/locale

# These are default values,
# Override when running container via docker(-compose)

# General ENV settings
ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    LC_ALL='en_US.UTF-8' \
    TZ='Etc/UTC' \
	DEB_PACKAGES="ca-certificates postgresql-client" \
	DEB_BUILD_DEPS="adduser" \
	ADMIN_NAME=admin \
	ADMIN_PWD=admin \
	ADMIN_EMAIL=admin.istrator@mydomain.com \
	SQLALCHEMY_DATABASE_URI='sqlite:////app/instance/DB/data.db' \
	SQLALCHEMY_ENGINE_OPTION_PRE_PING=False \
	SECRET_KEY='d544ccc37dc3ad214c09b1b7faaa64c60351d5c8bb48b342' \
	GHC_HOME=/app \
	GHC_USER=ghc \
	GHC_USER_HOME=/home/ghc \
	GHC_PROBE_HTTP_TIMEOUT_SECS=30 \
	GHC_MINIMAL_RUN_FREQUENCY_MINS=10 \
	GHC_RETENTION_DAYS=30 \
	GHC_SELF_REGISTER=False \
	GHC_NOTIFICATIONS=False \
	GHC_NOTIFICATIONS_VERBOSITY=True \
	GHC_WWW_LINK_EXCEPTION_CHECK=False \
	GHC_LARGE_XML=False \
	GHC_ADMIN_EMAIL='you@example.com' \
	GHC_RUNNER_IN_WEBAPP=False \
	GHC_REQUIRE_WEBAPP_AUTH=False \
	GHC_BASIC_AUTH_DISABLED=False \
	GHC_VERIFY_SSL=True \
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
	GHC_GEOIP_URL='http://ip-api.com/json/{hostname}' \
	GHC_GEOIP_LATFIELD='lat' \
	GHC_GEOIP_LONFIELD='lon' \
	GHC_METADATA_CACHE_SECS=900 \
    HOST=0.0.0.0 \
    PORT=80 \
    WSGI_WORKERS=4 \
    WSGI_WORKER_TIMEOUT=6000 \
    WSGI_WORKER_CLASS='gevent' \
    GHC_USER_PLUGINS=''

# GHC Core Plugins modules and/or classes, seldom needed to set:  \
# if not specified here or in Container environment  \
# all GHC built-in Plugins will be active.  \
#ENV GHC_PLUGINS 'GeoHealthCheck.plugins.probe.owsgetcaps,\
#        GeoHealthCheck.plugins.probe.wms, ...., ...\
#        GeoHealthCheck.plugins.check.checks' \

# GHC User Plugins, best be overridden via Container environment \

# Install operating system dependencies
RUN \
    apt update \
    && apt --no-install-recommends install -y ${DEB_PACKAGES} ${DEB_BUILD_DEPS} \
    && echo "For ${TZ} date=$(date)" && echo "Locale=$(locale)"  \
    && adduser --disabled-password --shell /bin/bash --gecos "User" ${GHC_USER} \
    && apt remove --purge -y ${DEB_BUILD_DEPS} \
    && apt clean \
    && apt autoremove -y  \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build --chown=${GHC_USER}:${GHC_USER} /app /app

# For later: run as user 'ghc'
USER ${GHC_USER}

EXPOSE ${PORT}

ENTRYPOINT [ "/app/docker/scripts/run-web.sh"  ]
