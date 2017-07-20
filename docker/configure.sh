#!/bin/bash
# Sets up various stuff in Docker Container: database and Plugins

echo "START /configure.sh"

cd /venv/ && . bin/activate

# Determine database type from DB URI
DB_TYPE=$(echo ${SQLALCHEMY_DATABASE_URI} | cut -f1 -d:)
echo "Using DB_TYPE=${DB_TYPE}"

# Create DB shorthand
function create_db() {
	pushd /GeoHealthCheck/
	paver create -u ${ADMIN_NAME} -p ${ADMIN_PWD} -e ${ADMIN_EMAIL}
	popd
}

# Init actions per DB type
case ${DB_TYPE} in

	sqlite)
		if [ ! -f /GeoHealthCheck/DB/data.db ]
		then
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
		echo "Check if Postgres is available..."
		until psql -h "${DB_HOST}" -U "${DB_USER}" -c '\l'; do
		  echo "Postgres is unavailable - sleeping"
		  sleep 1
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
	cp -ar /plugins/* /GeoHealthCheck/GeoHealthCheck/plugins/
fi

echo "END /configure.sh"
