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


# Complete the Docker tasks (only if this is a tagged release):
if [ -z ${TRAVIS_TAG} ]; then
  exit 0
fi


docker tag netflixoss/hubcommander:${TRAVIS_TAG} netflixoss/hubcommander:latest
docker images
docker login -u=${dockerhubUsername} -p=${dockerhubPassword}
docker push netflixoss/hubcommander:$TRAVIS_TAG
docker push netflixoss/hubcommander:latest
