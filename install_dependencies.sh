#!/bin/bash

# Update the package lists for upgrades and new package installations
apt-get update

# Install Python3 and pip3
apt-get install -y python3 python3-pip

# Install necessary Python packages
pip3 install pyvmom