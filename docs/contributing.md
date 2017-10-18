Contributing
=======================
Contributions to HubCommander are always welcome! :)

This doc contains some tips that can help get you up and running.


First things first...
----------------------
Please review the [installation documentation here first](installation.md). 
This will give you an understanding on what is required for HubCommander to function.


Development Setup
----------------
HubCommander is a Python 3 application, and as such, having a good Python 3 environment up and running is essential.

Google has very good documentation on setting up a Python environment [here](https://cloud.google.com/python/setup). 
(You don't need to set up the Google Cloud dependencies -- unless you want to do really cool GCP chatopcy things with HubCommander.)

You will also need to install `git`.  Some good guides on `git` can be found [here](https://git-scm.com/documentation).

To write Python, you can take your pick from various different text editors, such as [PyCharm](https://www.jetbrains.com/pycharm/), 
[Atom](https://atom.io), or [VS Code](https://code.visualstudio.com/) to name a few.

A section of debugging HubCommander in PyCharm [is available here](pycharm_debugging.md).

### Slack Setup
You can't write and test a Slack bot without Slack. For this, you will need a workspace on Slack (you can create one for free).
Once you have a workspace set up, you will need to create a channel. We recommend creating a testing channel for HubCommander for you
to issue test commands on.

At this point, follow [Slack's documentation here](https://api.slack.com/bot-users) to create a bot user for your workspace. This bot user
will need to be a member of the channel you want it to listen to commands on. 

You will also need to fetch a Slack token for this bot. Keep this token in a safe place where you can fetch it later. 
You can always regenerate a new one, but the token is essentially a password that will grant anyone who possesses it access to your Slack resources -- so keep it secure!

### GitHub Setup
The installation documentation includes the required instructions to get GitHub credentials. If you do not wish to use HubCommander to develop
against GitHub, then you can skip this. 

Fetch the code
----------------
To fetch the code for development, fork this repository, and `git clone` your fork. For more details on this, please review 
[GitHub's documentation here](https://help.github.com/articles/fork-a-repo/).

All development on HubCommander should be based upon the `develop` branch.

### Get the code working 
To get HubCommander working in your development environment, you will need to install all of its dependencies. Fortunately, we have included a
`basic_install.sh` file that should do all the hard work for you :)

To summarize, this will fetch [Slack's Python rtmbot](https://github.com/slackapi/python-rtmbot) version 
[0.4.0](https://github.com/slackapi/python-rtmbot/releases/tag/0.4.0) plugin -- which HubCommander 
depends on -- and it will then set up the virtual environments with all the dependencies installed.

To do this, follow these steps:
1. Fire up a Bash terminal
1. Navigate to any directory that you want to use for development
1. Follow the installation guide to install all the required dependencies (for OS X and Linux) [here](installation.md#install-the-bot)
1. Once installed, all files related to HubCommander will be placed in the `python-rtmbot-0.4.0/hubcommander` directory. `cd` to this directory.
1. Modify the `rtmbot.conf` file to include your Slack token obtained from the instructions above
1. Activate your virtual environment by running `source venv/bin/activate`
1. By default the HubCommander plugin wants the Slack token as a environment variable. You need to export it by running `export SLACK_TOKEN=YOUR-TOKEN-HERE`.
1. OPTIONAL: If you want to use HubCommander for GitHub and have created a token, you can export that via: `export GITHUB_TOKEN=YOUR-TOKEN-HERE`
1. You can now run a very basic bot by running `rtmbot`
1. You can test that it's working properly by navigating to the Slack channel you created and invited HubCommander to and issuing a `!help` command.
1. The "Repeat" plugin is also enabled by default, you can test that it works by running `!repeat Hello World!`.

### Install the unit test requirements
There are a few more steps to do before you can start developing:
1. Navigate to the `python-rtmbot-0.4.0/hubcommander` directory
1. Run: `git checkout -- .` (this will restore things like unit tests and which were removed by the `basic_install.sh` script)
1. Run: `pip install -r test-requirements.txt` to install the unit test dependencies
1. Verify that things are working by running `py.test tests`. You should see the unit tests pass.


Developing new features
-----------------
To write new features for HubCommander, please review the [plugin documentation here](making_plugins.md). This should provide all the information required to get you developing
features. Also, as a pointer, please take a look at existing plugins to get a feel for how they operate. Don't be afraid to copy and paste!

Some other things to consider:
1. Develop Python code that follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) coding standards (this is where PyCharm and other Python editors can come in handy)
1. Develop against the `develop` branch
1. Write unit tests! (This is something we need to improve)
1. Be careful of committing secrets!!
1. Submit PRs back against the `develop` branch
1. Keep feature requests small. It will make it easier to develop and merge things in.


Where can I find help?
--------------------
If you are stuck and need assistance, please feel free to reach out to us on [Gitter](https://gitter.im/Netflix/hubcommander).
Alternatively, you can file an issue here on GitHub, and we'll be sure to assist!
