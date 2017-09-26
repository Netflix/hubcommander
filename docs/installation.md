HubCommander Installation
=====================

The steps below make the following assumptions:
* You are using Linux or macOS
* Have Python 3.5 installed
* Have a GitHub organization to manage
* Have a GitHub user with `owner` privileges.
* Have Slack API credentials
* Have a Slack Channel dedicated for running the bot in
* **Preferably have a means of protecting secrets -- you will need to write some code here!**

Basic Installation
-----------------
HubCommander is dependent on the [slackhq/python-rtmbot](https://github.com/slackhq/python-rtmbot) 
release [0.4.0](https://github.com/slackhq/python-rtmbot/releases/tag/0.4.0)). Please review details about the
python-rtmbot before continuing to install HubCommander.

The python-rtmbot typically operates by placing a plugin in the `plugins` directory.

A docker image for HubCommander is provided to help get up and running as fast as possible. Alternatively, 
a shell script is provided [here](https://github.com/Netflix/hubcommander/blob/master/basic_install.sh)
that will fetch the rtmbot, and will `git clone` HubCommander into the `plugins` directory.

Once that is done, you will need to perform all additional configuration steps required to nake it function in your
environment, including credential management.

Install the bot
--------------

### For Docker:

Continue reading this document first. Once done, continue reading the Docker details (linked below).

### For macOS:

1. Install [Homebrew](http://brew.sh)
2. Install Python 3.5+: `brew install python3`
3. Proceed to "Continued Instructions"

### For Ubuntu or other Linuxes:

1. Run `sudo apt-get update`
2. Run `sudo apt-get install python3 python3-venv curl git -y`
3. Proceed to "Continued Instructions"

### Continued Instructions

1. Clone the HubCommander git repository: `git clone git@github.com:Netflix/hubcommander.git`.
2. Run the following commands:

   ```
   chmod +x hubcommander/basic_install.sh
   ./hubcommander/basic_install.sh
   ```
3. Proceed to "Configuration"

## OPTIONAL for unit tests:
If you are installing for development you will need to install the testing dependencies. 
Follow the `Install the unit test requirements` section of the [contributing guide](contributing.md#install-the-unit-test-requirements) for details.


Configuration
--------------

The primary steps for configuration center around credential management for Slack, and GitHub
(and optionally Travis CI and Duo if you utilize those services).

### Decrypting secrets

Out of the box, HubCommander is configured to receive secrets from environment variables. This is provided
to simplify running HubCommander in Docker. These secrets should not be stored at rest unencrypted.

HubCommander also provides an [AWS KMS](https://aws.amazon.com/kms/) method for extracting an encrypted
JSON blob that contains the secrets.

**If your organization utilizes a different mechanism for encrypting credentials, you will need to add code 
to [`decrypted_creds.py`](https://github.com/Netflix/hubcommander/blob/master/decrypt_creds.py)'s
`get_credentials()` function.** __Please DO NOT store credentials and tokens in plaintext here!__

No matter the encryption mechanism utilized, all secrets are passed into each plugin's `setup()` method, which
enable the plugins to make authenticated calls to their respective services. You must get the credentials 
required for plugins to work.

1. Contact your Slack administrator to obtain a Slack token that can be used for bots.
2. If you haven't already, create a GitHub bot account, and invite it to all the organizations that 
   you manage with the `owner` role. Also, please configure this account with a strong password
   and 2FA! (Don't forget to back up those recovery codes into a safe place!)

### GitHub Configuration

Each plugin in HubCommander typically has a `config.py` file. This is where you can place in any additional
configuration that the plugin supports.

For the GitHub plugin, you are required to define a Python `dict` with the organizations that you manage. An example
of what this `dict` looks like can be found in the sample
[`github/config.py`](https://github.com/Netflix/hubcommander/blob/master/github/config.py) file.

At a minimum, you need to specify the real name of the organization, a list of aliases for the orgs (or an empty list),
whether the organization can only create public repos (via the `public_only` boolean), as well as 
a list of `dicts` that define the teams specific to the organization for new repositories will be assigned with. 
This `dict` consists of 3 parts:
the `id` of the GitHub org's team (you can get this from the
[`list_teams`](https://developer.github.com/v3/orgs/teams/#list-teams) GitHub API command, along with the 
permission for that team to have on newly created repos (either `pull`, `push`, or `admin`),
as well as the actual `name` of the team.

#### GitHub Configuration: API Token

Once you have a GitHub bot user account available, it is time to generate an API token. This will be used
by HubCommander to perform privileged GitHub tasks.

You will need to create an [access token](https://help.github.com/articles/creating-an-access-token-for-command-line-use/).
To do this, you will need to:

1. Log into your GitHub bot user's account.
2. Visit [this settings page](https://github.com/settings/tokens) to see the `Personal Access Tokens`
3. Click `Generate new token`.
4. Provide a description for this token, such as `HubCommander Slack GitHub Bot API token`.
5. Provide the following scopes:

   - `repo` (All)
   - `read:org`
   - `write:org`
   - `delete_repo`
   - (These scopes can be later modified)

6. Click `Generate Token` to get the API key. This will only be displayed once. You can always re-generate 
   a new token, but you will need to modify your HubCommander configuration each time you do.

### HubCommander Secrets

Once you have your GitHub and Slack Tokens, you are now ready to configure HubCommander (if you wish to make use
of Travis CI and Duo integration, please refer to the docs for those plugins
[here](travis_ci.md) and [here](authentication.md)).

You will need to encrypt the Slack and GitHub credentials. If you make use of AWS, a KMS example is provided 
in [`decrypted_creds.py`](https://github.com/Netflix/hubcommander/blob/master/decrypt_creds.py).

At a minimum, HubCommander requires the following secrets (as a Python `dict`):
```
{
    "SLACK": "Your slack token here...",
    "GITHUB": "Your GitHub API token here..."
}
```

Encrypt this via any desirable means you choose, and add in your decryption code to the `get_credentials()` function.

*Note:* You will need to ensure that the rtmbot's Slack credentials are also encrypted (this requires the 
same Slack token). Use whatever deployment mechanism you have in place to ensure that it is encrypted and 
in a safe place before running the application.

## Additional Command Configuration

Please refer to the documentation [here](command_config.md) for additional details.

Running HubCommander
-------------------

### `rtmbot` Configuration

Regardless of how you run the bot, you will need to worry about the `rtmbot` configuration. The factory docker image
generates this dynamically, but if you decide to make changes to the image, you will need to be aware of how
this works.

The `rtmbot.conf` file is required to be placed in the base directory of the `rtmbot`.  This file MUST have some 
elements in it. Namely, it must look similar to this:

```
DEBUG: True
SLACK_TOKEN: "YOUR-SLACK-TOKEN-HERE"
ACTIVE_PLUGINS:
    - hubcommander.hubcommander.HubCommander
```


### Using Docker

Continue reading the [HubCommander Docker documentation here](docker.md).

### Not using Docker

If you ran the installation shell script, and made all the configuration file changes you need, then you
are ready to run this!

You will simply follow the instructions for running the python-rtmbot, which is typically to run:
```
# Activate your venv:
source /path/to/venv/.../bin/activate
rtmbot
```
If all is successful, you should see no errors in the output, and your bot should appear in the Slack channel
that it was configured to run in.

Test that it works by running `!Help`, and `!ListOrgs`.
