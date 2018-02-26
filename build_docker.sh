#!/bin/bash

################################################################################
#
#
#  Copyright 2017 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
#
################################################################################

# This will build a docker image of HubCommander.

if [ -z ${BUILD_TAG} ]; then
  BUILD_TAG="latest"
fi

# If this is running in Travis, AND the Python version IS NOT 3.6, then don't build
# the Docker image:
if [ $TRAVIS ]; then
    PYTHON_VERSION=$( python --version )
    if [[ $PYTHON_VERSION != *"3.6"* ]]; then
        echo "This only builds Docker images in the Python 3.6 Travis job"
        exit 0
    fi
fi

export RTM_VERSION="0.4.0"
export RTM_PATH="python-rtmbot-${RTM_VERSION}"

echo "-----------------------------------------"
echo "HubCommander Docker builder"
echo "-----------------------------------------"

# Download the RTM bot:
echo "[-->] Grabbing the Python RTM Bot first..."
curl -L https://github.com/slackhq/python-rtmbot/archive/${RTM_VERSION}.tar.gz > ${RTM_PATH}.tar.gz
echo "[+] Completed download"

# Build the Docker image... the Dockerfile will do the rest:
echo "[-->] Now building the Docker image..."


# Build that Docker image...
docker build  -t netflixoss/hubcommander:${BUILD_TAG} --rm=true . --build-arg RTM_VERSION=${RTM_VERSION}

cmd_st="$?"
if [ $cmd_st -gt 0 ]
then
  echo "Error building image. Exiting."
  exit $cmd_st
fi

echo
echo "DONE!"
