FROM ubuntu:xenial

# Mostly Mike Grima: mgrima@netflix.com
MAINTAINER NetflixOSS <netflixoss@netflix.com>

# Install the Python RTM bot itself:
ARG RTM_VERSION
ADD python-rtmbot-${RTM_VERSION}.tar.gz /

# Add all the other stuff to the plugins:
COPY / /python-rtmbot-${RTM_VERSION}/plugins

# Install all the things:
RUN \
  # Rename the rtmbot:
  mv /python-rtmbot-${RTM_VERSION} /hubcommander && \

  # Install Python:
  apt-get update && \
  apt-get upgrade -y && \
  apt-get install python3 python3-venv nano -y && \

  # Set up the VENV:
  pyvenv /venv && \

  # Install all the deps:
  /bin/bash -c "source /venv/bin/activate && pip install --upgrade pip" && \
  /bin/bash -c "source /venv/bin/activate && pip install wheel" && \
  /bin/bash -c "source /venv/bin/activate && pip install -r /hubcommander/requirements.txt" && \
  /bin/bash -c "source /venv/bin/activate && pip install -r /hubcommander/plugins/requirements.txt" && \

  # The launcher script:
  mv /hubcommander/plugins/launch_in_docker.sh / && chmod +x /launch_in_docker.sh && \
  rm /hubcommander/plugins/python-rtmbot-${RTM_VERSION}.tar.gz

# DEFINE YOUR ENV VARS FOR SECRETS HERE:
ENV SLACK_TOKEN="REPLACEMEINCMDLINE" \
    GITHUB_TOKEN="REPLACEMEINCMDLINE" \
    TRAVIS_PRO_USER="REPLACEMEINCMDLINE" \
    TRAVIS_PRO_ID="REPLACEMEINCMDLINE" \
    TRAVIS_PRO_TOKEN="REPLACEMEINCMDLINE" \
    TRAVIS_PUBLIC_USER="REPLACEMEINCMDLINE" \
    TRAVIS_PUBLIC_ID="REPLACEMEINCMDLINE" \
    TRAVIS_PUBLIC_TOKEN="REPLACEMEINCMDLINE" \
    DUO_HOST="REPLACEMEINCMDLINE" \
    DUO_IKEY="REPLACEMEINCMDLINE" \
    DUO_SKEY="REPLACEMEINCMDLINE"

# Installation complete!  Ensure that things can run properly:
ENTRYPOINT ["/bin/bash", "-c", "./launch_in_docker.sh"]
