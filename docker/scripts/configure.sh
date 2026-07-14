#!/bin/bash
# Sets up various stuff in Docker Container: database and Plugins

echo "START configure.sh"
pushd /app  || exit 1
source pixi-env.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/app/GeoHealthCheck:$PYTHONPATH

# Determine database type from DB URI
DB_TYPE=$(echo ${SQLALCHEMY_DATABASE_URI} | cut -f1 -d:)
echo "Using DB_TYPE=${DB_TYPE}"

# Create DB shorthand
function create_db() {
  invoke create -u ${ADMIN_NAME} -p ${ADMIN_PWD} -e ${ADMIN_EMAIL}
}

# Init actions per DB type
case ${DB_TYPE} in

	sqlite)
	  if ! [ -f /app/instance/DB/data.db ]; then
			echo "Creating SQLite DB tables..."
			create_db
		else
			echo "NOT creating SQLite DB tables..."
		fi
	    ;;

	postgresql)
		# format: postgresql://user:pw@host:5432/db
		# Bit tricky, may use awk, but cut out DB elements from URI
		DB_NAME=$(echo ${SQLALCHEMY_DATABASE_URI} | cut -f4 -d/)
		DB_PASSWD_HOST=$(echo ${SQLALCHEMY_DATABASE_URI} | cut -f3 -d:)
    DB_HOST=$(echo ${DB_PASSWD_HOST} | cut -f2 -d@)
    DB_PASSWD=$(echo ${DB_PASSWD_HOST} | cut -f1 -d@)
    DB_USER_SLASH=$(echo ${SQLALCHEMY_DATABASE_URI} | cut -f2 -d:)
    DB_USER=$(echo ${DB_USER_SLASH} | cut -f3 -d/)
		export PGPASSWORD=${DB_PASSWD}

		# We need to wait until PG Container available
		echo "Check if Postgres is avail/ready..."
		until pg_isready -h "${DB_HOST}"; do
		  echo "Exit code=$? - Postgres not ready - sleeping"
		  sleep $[ ( $RANDOM % 6 )  + 1 ]s
		done

		# Check if we need to create DB tables
		echo "Postgres is up - check if DB populated"
		if ! psql -h "${DB_HOST}" -U "${DB_USER}" -c 'SELECT COUNT(*) FROM resource' ${DB_NAME}
		then
			echo "Creating Postgres DB tables..."
			create_db
		else
			echo "Postgres DB already populated"
		fi

	    ;;
	*)
		echo "Unknown database type ${DB_TYPE}, exiting"
		exit -1
	  ;;
esac

# Copy possible mounted Plugins into app tree
if [ -d /plugins ]
then
	cp -ar /plugins/* ${GHC_HOME}/GeoHealthCheck/plugins/
fi

echo "END configure.sh"
