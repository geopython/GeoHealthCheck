#!/bin/bash

# Set timezone and time right in container.
# See: https://www.ivankrizsan.se/2015/10/31/time-in-docker-containers/ (Alpine)

# Set the timezone. Base image does not contain
# the setup-timezone script, so an alternate way is used.
if [ "$CONTAINER_TIMEZONE" = "" ];
then
	CONTAINER_TIMEZONE="Europe/London"
else
	echo "Container timezone not modified"
fi

cp /usr/share/zoneinfo/${CONTAINER_TIMEZONE} /etc/localtime && \
echo "${CONTAINER_TIMEZONE}" >  /etc/timezone && \
echo "Container timezone set to: $CONTAINER_TIMEZONE"

# Force immediate synchronisation of the time and start the time-synchronization service.
# In order to be able to use ntpd in the container, it must be run with the SYS_TIME capability.
# In addition you may want to add the SYS_NICE capability,
# in order for ntpd to be able to modify its priority.
# ntpd -s
