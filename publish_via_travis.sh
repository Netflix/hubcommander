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

# If this is running in Travis, AND the Python version IS NOT 3.5, then don't build
# the Docker image:
if [ $TRAVIS ]; then
    PYTHON_VERSION=$( python --version )
    if [[ $PYTHON_VERSION != *"3.5"* ]]; then
        echo "This only publishes Docker images in the Python 3.5 Travis job"
        exit 0
    fi
else
    echo "This can only be run from Travis CI. Exiting..."
    exit -1
fi

# Complete the Docker tasks (only if this is a tagged release):
if [ -z ${TRAVIS_TAG} ]; then
  echo "Not publishing to Docker Hub, because this is not a tagged release."
  exit 0
fi

echo "TAGGED RELEASE: ${TRAVIS_TAG}, publishing to Docker Hub..."

docker tag netflixoss/hubcommander:${TRAVIS_TAG} netflixoss/hubcommander:latest
docker images
docker login -u=${dockerhubUsername} -p=${dockerhubPassword}
docker push netflixoss/hubcommander:$TRAVIS_TAG
docker push netflixoss/hubcommander:latest

echo "Completed publishing to Docker Hub."
