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
echo 'DEBUG: True' > /rtmbot/rtmbot.conf
echo 'SLACK_TOKEN: "'$SLACK_TOKEN'"' >> /rtmbot/rtmbot.conf
echo 'ACTIVE_PLUGINS:' >> /rtmbot/rtmbot.conf
echo '    - hubcommander.hubcommander.HubCommander' >> /rtmbot/rtmbot.conf

# Launch it!
export PYTHONIOENCODING="UTF-8"
source venv/bin/activate
cd /rtmbot
rtmbot
