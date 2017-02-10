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
# This will first download and extract the slackhq/python-rtmbot, and then fetch
# HubCommander into the plugins directory.

# After the files are fetched, the script will attempt to create the python virtual
# environments and install all the python dependencies (PYTHON 3.5+ IS REQUIRED!)

RTM_VERSION="0.3.0"
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

if command -v pyvenv >/dev/null 2>&1 ; then

  PYTHON_VERSION=`python --version 2>&1 | grep -i continuum`
  if [[ $PYTHON_VERSION != "" ]]; then
      echo "[+] Conda installation detected ..."
      pyvenv venv --without-pip
      source venv/bin/activate


      echo "[-->] Installing PIP in venv..."
      curl -O https://bootstrap.pypa.io/get-pip.py
      python get-pip.py
      echo "[+] PIP Installed"
  else
      pyvenv venv
      source venv/bin/activate
  fi

  echo "[+] Created venv"
  # Install the dependencies for the rtmbot:
  echo "[-->] Installing rtmbot's dependencies..."
  pip install wheel
  pip install -r requirements.txt
  echo "[+] Completed installing rtmbot dependencies."


  # Install HubCommander
  echo "[-->] Moving HubCommander to the plugins dir..."
  mv ../hubcommander/* plugins/
  rm -Rf ../hubcommander
  echo "[+] Completed moving HubCommander to the plugins dir."

  # Install the dependencies for HubCommander:
  echo "[-->] Installing HubCommander' dependencies..."
  pip install -r plugins/requirements.txt
  echo "[+] Completed installing HubCommander' dependencies."

  echo "-------- What's left to do? --------"
  echo "At this point, you will need to create a 'rtmbot.conf' file as per the instructions for the rtmbot."
  echo "Additionally, you will need to perform all of the remaining configuration that is required for"
  echo "HubCommander. Please review the instructions for details."

  echo
  echo "DONE!"
else
  echo "pyvenv is not installed. Install pyvenv to continue. Aborting."
  exit 1;
fi

