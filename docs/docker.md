HubCommander Docker Image
====================

HubCommander has a Docker image to help you get up and running as quickly and easily as possible.

The image can be found on Docker Hub [here](https://hub.docker.com/r/netflixoss/hubcommander/). Alternatively,
a [`Dockerfile`](https://github.com/Netflix/hubcommander/blob/master/Dockerfile) is included should you want to make your own image.

## Fetching the Docker image

Run `docker pull netflixoss/hubcommander:latest` to fetch and install the Docker Hub image.

## Running the Docker image

The docker image is configured to have secrets for Slack, GitHub, Duo (optional), and Travis CI (optional) passed in
as environment variables passed in from `docker run`.

Additionally, HubCommander requires other configuration files to be modified outside of the Docker image, and mounted
into the image.  An example of this is the [`github/config.py`](https://github.com/Netflix/hubcommander/blob/master/github/config.py) file.

Here is an example of running HubCommander with the Duo plugin:
```
docker run -d \
 -e "SLACK_TOKEN=SOME_SLACK_TOKEN" \
 -e "GITHUB_TOKEN=SOME_GITHUB_TOKEN" \
 -e "DUO_HOST=SOME_DUO_HOST.duosecurity.com" \
 -e "DUO_IKEY=SOME_DUO_IKEY" \
 -e "DUO_SKEY=SOME_DUO_SKEY" \
 -v /path/to/cloned/hubcommander/auth_plugins/enabled_plugins.py:/rtmbot/hubcommander/auth_plugins/enabled_plugins.py \
 -v /path/to/cloned/hubcommander/github/config.py:/rtmbot/hubcommander/github/config.py \
 netflixoss/hubcommander:latest
```

The above commands passes in the secrets for Slack, GitHub, and Duo via environment variables. The 
[`auth_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/auth_plugins/enabled_plugins.py)
is modified to enable Duo, and mounted into the image.

An alternative to mounting configuration files into the image is to modify the source files directly, and run the 
[`build_docker.sh`](https://github.com/Netflix/hubcommander/blob/master/build_docker.sh) script to re-build the Docker
image to your specifications.
