#!/bin/bash

# from https://pythonspeed.com/articles/system-packages-docker/

# Bash "strict mode", to help catch problems and bugs in the shell
# script. Every bash script you write should include this. See
# http://redsymbol.net/articles/unofficial-bash-strict-mode/ for
# details.
set -euo pipefail

# 32-bit Wine requires i386
dpkg --add-architecture i386

# Tell apt-get we're never going to be able to give manual
# feedback:
export DEBIAN_FRONTEND=noninteractive

# Update the package listing, so we know what package exist:
apt-get update

# Install security updates:
apt-get --yes upgrade

# Install a new package, without unnecessary recommended packages:
apt-get --yes install --no-install-recommends "$@"

# Delete cached files we don't need anymore:
apt-get clean
rm -rf /var/lib/apt/lists/*
