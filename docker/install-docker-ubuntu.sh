#!/bin/bash
#
# This prepares an empty Ubuntu system for running Docker.
#
# Just van den Broecke - 2017
# DEPRECATED - 2021 update:  there are much quicker ways
# See https://docs.docker.com/engine/install/ubuntu/
#
# Below was based on
# https://docs.docker.com/engine/installation/linux/ubuntu/
# as on may 26 2017.
# Run as root or prepend all commands with "sudo"!
#

# Optional, comment out for your locale
# set time right and configure timezone and locale
# echo "Europe/Amsterdam" > /etc/timezone
# dpkg-reconfigure -f noninteractive tzdata

# Bring system uptodate
apt-get update
apt-get -y upgrade

# Install packages to allow apt to use a repository over HTTPS
apt-get install -y software-properties-common apt-transport-https ca-certificates curl

# Add keys and extra repos
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Verify key
apt-key fingerprint 0EBFCD88

# Add Docker repo to deb config
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

# Bring packages uptodate
apt-get update

# The linux-image-extra package allows you use the aufs storage driver.
# at popup keep locally installed config option
# apt-get install -y linux-image-extra-$(uname -r)
apt-get install -y linux-image-extra-$(uname -r) linux-image-extra-virtual

# https://askubuntu.com/questions/98416/error-kernel-headers-not-found-but-they-are-in-place
apt-get install -y build-essential linux-headers-`uname -r` dkms

# Install Docker CE
apt-get install docker-ce

# If you are installing on Ubuntu 14.04 or 12.04, apparmor is required.
# You can install it using (usually already installed)
# apt-get install -y apparmor

# Start the docker daemon. Usually already running
# service docker start

# Docker compose
export dockerComposeVersion="1.20.1"
curl -L https://github.com/docker/compose/releases/download/${dockerComposeVersion}/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
