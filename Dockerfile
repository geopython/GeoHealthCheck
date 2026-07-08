FROM ghcr.io/prefix-dev/pixi:0.72.0-noble

# Credits to yjacolin for providing first versions
LABEL original_developer="yjacolin <yves.jacolin@camptocamp.com>" \
	maintainer="Just van den Broecke <justb4@gmail.com>"

# These are default values,
# Override when running container via docker(-compose)

# ARGS
ARG TZ="Etc/UTC"
ARG LANG="en_US.UTF-8"
ARG ADD_DEB_PACKAGES=""

# General ENV settings
ENV LC_ALL="en_US.UTF-8" \
	LANG="en_US.UTF-8" \
	LANGUAGE="en_US.UTF-8" \
    \
	\
	DEB_PACKAGES="ca-certificates locales postgresql-client" \
	DEB_BUILD_DEPS="curl adduser" \
	ADMIN_NAME=admin \
	ADMIN_PWD=admin \
	ADMIN_EMAIL=admin.istrator@mydomain.com \
	SQLALCHEMY_DATABASE_URI='sqlite:////GeoHealthCheck/DB/data.db' \
	SQLALCHEMY_ENGINE_OPTION_PRE_PING=False \
	SECRET_KEY='d544ccc37dc3ad214c09b1b7faaa64c60351d5c8bb48b342' \
	GHC_HOME=/GeoHealthCheck \
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
    \
# WSGI server settings, assumed is gunicorn  \
HOST=0.0.0.0 \
PORT=80 \
WSGI_WORKERS=4 \
WSGI_WORKER_TIMEOUT=6000 \
WSGI_WORKER_CLASS='gevent' \
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

# Add standard files and Add/override Plugins
# Alternative Entrypoints to run GHC jobs
# Override default Entrypoint with these on Containers
COPY docker/scripts/*.sh docker/config_site.py docker/plugins /

# Add Source Code
COPY . ${GHC_HOME}

WORKDIR ${GHC_HOME}

# Install operating system dependencies
RUN \
    apt-get update \
    && apt-get --no-install-recommends install -y ${DEB_PACKAGES} ${DEB_BUILD_DEPS} ${ADD_DEB_PACKAGES} \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
    && echo "For ${TZ} date=$(date)" && echo "Locale=$(locale)"  \
    && adduser --disabled-password --shell /bin/bash --home ${GHC_HOME} --gecos "User" ghc \
    && chmod +x /*.sh  \
    && pixi install --locked -e prod \
    && pixi run -e prod setup \
    && cp /config_site.py ${GHC_HOME}/instance/config_site.py \
    && if [ -d /plugins ]; then cp -ar /plugins/* ${GHC_HOME}/GeoHealthCheck/plugins/; fi && rm -rf /plugins \
    && apt-get remove --purge -y ${DEB_BUILD_DEPS} \
    && apt-get clean \
    && apt autoremove -y  \
    && rm -rf /var/lib/apt/lists/*

# For later: run as user 'ghc'
# USER ghc

# For SQLite
VOLUME ["/GeoHealthCheck/DB/"]

EXPOSE ${PORT}

ENTRYPOINT /run-web.sh
