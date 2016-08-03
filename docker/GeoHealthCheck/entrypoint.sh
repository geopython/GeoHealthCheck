#!/bin/bash
cd /venv/ && . bin/activate
if [ ! -f /GeoHealthCheck/DB/data.db ]
then
  cd /GeoHealthCheck/
  paver create -u ${ADMIN_NAME} -p ${ADMIN_PWD} -e ${ADMIN_EMAIL}
  cd -
fi

python /GeoHealthCheck/GeoHealthCheck/app.py ${HOST}:${PORT}