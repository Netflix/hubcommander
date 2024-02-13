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

# This is a quick-and-dirty script to install HubCommander.
# This will first download and extract the slackhq/python-rtmbot, and then place
# HubCommander into the proper directory path.

# After the files are fetched, the script will attempt to create the python virtual
# environments and install all the python dependencies (PYTHON 3.5+ IS REQUIRED!)

# You MUST run this from the parent directory that contains this script. So, if this
# script is in a directory named "hubcommander", you must run this from:
# ../hubcommander so that you issue: ./hubcommander/basic_install.sh

echo "Checking if I am able to CD into the proper directory..."
cd hubcommander
if [ $? -ne 0 ]; then
    echo "[X] DIRECTORY PATHS ARE WRONG. Source directory needs to be named 'hubcommander' and you"
    echo "    must run this from the parent directory of 'hubcommander'!!"
    exit -1
fi
cd ..
RTM_VERSION="0.4.0"
RTM_PATH="python-rtmbot-${RTM_VERSION}"
echo "Installing HubCommander and all dependencies..."

# Fetch the python-rtmbot in the parent directory of this one:
echo "[-->] Downloading the RTM bot to: $( pwd )"
curl -L https://github.com/slackhq/python-rtmbot/archive/${RTM_VERSION}.tar.gz > ${RTM_PATH}.tar.gz
echo "[+] Completed download"

# Extract:
echo "[-->] Extracting the RTM bot..."
tar xvf ${RTM_PATH}.tar.gz
cd ${RTM_PATH}
echo "[+] Completed extracted RTM bot"

# Create the virtualenvs:
echo "[-->] Creating venv in ${RTM_PATH}..."

if command -v python3 >/dev/null 2>&1 ; then

  PYTHON_VERSION=`python3 --version 2>&1 | grep -i continuum`
  if [[ $PYTHON_VERSION != "" ]]; then
      echo "[+] Conda installation detected ..."
      python3 -m venv venv --without-pip
      source venv/bin/activate

      echo "[-->] Installing PIP in venv..."
      curl -O https://bootstrap.pypa.io/get-pip.py
      python3 get-pip.py
      echo "[+] PIP Installed"
  else
      python3 -m venv venv
      source venv/bin/activate
  fi

  echo "[+] Created venv"

  # Install HubCommander
  echo "[-->] Moving HubCommander to the correct dir..."
  mv ../hubcommander hubcommander/
  echo "[+] Completed moving HubCommander to the correct dir."

  # Install the dependencies for the rtmbot:
  echo "[-->] Installing rtmbot's dependencies..."
  pip install wheel
  pip install ./hubcommander/
  echo "[+] Completed installing HubCommander's dependencies."

  # May not be relevant anymore -- but can't hurt:
  echo "[-->] Removing unnecessary files..."
  # Need to delete the "setup.py" file because it interferes with the rtmbot:
  rm -f hubcommander/setup.py
  # Need to delete the "tests/" directory, because it also interferes with the rtmbot:
  rm -Rf hubcommander/tests
  echo "[-] Completed unnecessary file removal."

  # Make a skeleton of the rtmbot.conf file:
  echo "[-->] Creating the skeleton 'rtmbot.conf' file..."
  echo 'DEBUG: True' > rtmbot.conf
  echo 'SLACK_TOKEN: "'PLACE SLACK TOKEN HERE'"' >> rtmbot.conf
  echo 'ACTIVE_PLUGINS:' >> rtmbot.conf
  echo '    - hubcommander.hubcommander.HubCommander' >> rtmbot.conf
  echo "[+] Completed the creation of the skeleton 'rtmbot.conf' file..."

  echo
  echo "-------- What's left to do? --------"
  echo "At this point, you will need to modify the 'rtmbot.conf' file as per the instructions for the rtmbot."
  echo "Additionally, you will need to perform all of the remaining configuration that is required for"
  echo "HubCommander. Please review the instructions for details."

  echo
  echo "DONE!"
else
  echo "python3 is not installed. Install python3 to continue. Aborting."
  exit 1;
fi
