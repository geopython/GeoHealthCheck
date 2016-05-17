#!/bin/bash

if [ ! -f /GeoHealthCheck/DB/data.db ]
then
  cd /GeoHealthCheck/
  /venv/bin/paver create -u ${ADMIN_NAME} -p ${ADMIN_PWD} -e ${ADMIN_EMAIL}
fi

/venv/bin/python /GeoHealthCheck/GeoHealthCheck/app.py ${HOST}:${PORT}