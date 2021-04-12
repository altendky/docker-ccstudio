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

#install universe so we can install more packages & update the package listing again
apt-get install -y software-properties-common
add-apt-repository universe          
apt-get update

#apt-get install -y tar

#download & install oclint (no apt-get)
#apt-get install -y wget
#apt-get install -y tar
#wget https://github.com/oclint/oclint/releases/download/v21.03/oclint-21.03-llvm-11.1.0-x86_64-linux-ubuntu-20.04.tar.gz
#tar -xf oclint-21.03-llvm-11.1.0-x86_64-linux-ubuntu-20.04.tar.gz

# Install security updates:
apt-get --yes upgrade

# Install a new package, without unnecessary recommended packages:
apt-get --yes install --no-install-recommends "$@"

# Delete cached files we don't need anymore:
apt-get clean
rm -rf /var/lib/apt/lists/*
