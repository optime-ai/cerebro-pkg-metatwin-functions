#!/bin/bash

NEXUS_REPOSITORY=https://nexus.optime-test-011.cerebro.optime.ai/repository/pypi-default/

# Set Nexus credentials (you'll need to provide these)
read -p "Enter Nexus username: " TWINE_USERNAME
read -s -p "Enter Nexus password: " TWINE_PASSWORD
echo
export TWINE_USERNAME
export TWINE_PASSWORD

read -p "Enter package version (ex. 0.0.1): " version
sed -i '' "s/version=.*[^,]/version='$version'/" setup.py
rm -rf dist cerebro_etl.egg-info
python -m build
twine upload --repository-url $NEXUS_REPOSITORY dist/* --verbose