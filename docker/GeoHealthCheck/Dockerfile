FROM debian:jessie
MAINTAINER yjacolin <yves.jacolin@camptocamp.com>

ENV ADMIN_NAME admin
ENV ADMIN_PWD admin
ENV ADMIN_EMAIL admin.istrator@mydomain.com
ENV SQLALCHEMY_DATABASE_URI 'sqlite:////GeoHealthCheck/DB/data.db'
ENV HOST 0.0.0.0
ENV PORT 80
ENV SECRET_KEY ��▒��Nx{P� zp$�W�V����
ENV GHC_RETENTION_DAYS 30
ENV GHC_RUN_FREQUENCY 'hourly'
ENV GHC_SELF_REGISTER False
ENV GHC_NOTIFICATIONS False
ENV GHC_ADMIN_EMAIL 'you@example.com'
ENV GHC_SITE_TITLE 'GeoHealthCheck Demonstration'
ENV GHC_SITE_URL 'http://localhost'
ENV GHC_SMTP_SERVER None
ENV GHC_SMTP_PORT None
ENV GHC_SMTP_TLS False
ENV GHC_SMTP_SSL False
ENV GHC_SMTP_USERNAME None
ENV GHC_SMTP_PASSWORD None

RUN apt-get update && \
    apt-get install -qqy virtualenv git python-pip python-dev vim && \
    apt-get autoremove -y ; apt-get clean ; \
    rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

ADD install.sh /install.sh
ADD entrypoint.sh /entrypoint.sh
ADD config_site.py /config_site.py
RUN bash install.sh

ADD cron-jobs-daily.sh /cron-jobs-daily.sh
ADD cron-jobs-hourly.sh /cron-jobs-hourly.sh
RUN chmod a+x /cron-jobs-daily.sh
RUN chmod a+x /cron-jobs-hourly.sh

VOLUME ["/GeoHealthCheck/DB/"]

EXPOSE ${PORT}

ENTRYPOINT /entrypoint.sh
