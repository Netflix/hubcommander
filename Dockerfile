FROM ubuntu:xenial

# Mostly Mike Grima: mgrima@netflix.com
MAINTAINER NetflixOSS <netflixoss@netflix.com>

RUN \
  # Install Python:
  apt-get update && \
  apt-get upgrade -y && \
  apt-get install python3 python3-venv nano curl -y

# Install the Python RTM bot itself:
ARG RTM_VERSION="0.4.0"
ARG RTM_PATH="python-rtmbot-${RTM_VERSION}"
RUN curl -L https://github.com/slackhq/python-rtmbot/archive/${RTM_VERSION}.tar.gz > /${RTM_PATH}.tar.gz && tar xvzf python-rtmbot-0.4.0.tar.gz


# Add all the other stuff to the plugins:
COPY / /python-rtmbot-${RTM_VERSION}/hubcommander

# Install all the things:
RUN \
  # Rename the rtmbot:
  mv /python-rtmbot-${RTM_VERSION} /rtmbot && \
  # Set up the VENV:
  pyvenv /venv && \
  # Install all the deps:
  /bin/bash -c "source /venv/bin/activate && pip install --upgrade pip" && \
  /bin/bash -c "source /venv/bin/activate && pip install --upgrade setuptools" && \
  /bin/bash -c "source /venv/bin/activate && pip install wheel" && \
  /bin/bash -c "source /venv/bin/activate && pip install /rtmbot/hubcommander" && \
  # The launcher script:
  mv /rtmbot/hubcommander/launch_in_docker.sh / && chmod +x /launch_in_docker.sh && \
  rm /python-rtmbot-${RTM_VERSION}.tar.gz

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
