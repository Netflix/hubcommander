HubCommander
=====================
[![NetflixOSS Lifecycle](https://img.shields.io/osslifecycle/Netflix/osstracker.svg)]()

A user-extendable Slack bot for GitHub organization management. 

HubCommander provides a chat-ops means for managing GitHub organizations. 
It creates a simple way to perform privileged GitHub organization management tasks without granting
administrative or `owner` privileges to your GitHub organization members.

How it works?
-------------
HubCommander is based on [slackhq/python-rtmbot](https://github.com/slackhq/python-rtmbot) 
(currently, dependent on release [0.3.0](https://github.com/slackhq/python-rtmbot/releases/tag/0.3.0))

You simply type `!help`, and the bot will output a list of commands that the bot supports. Typing
the name of the command, for example: `!CreateRepo`, will output help text on how to execute the command.

At a minimum, you will need to have the following:
* Python 3.5+
* Slack and Slack credentials
* A GitHub organization
* A GitHub bot user with ownership level privileges

A Docker image is also available to help get up and running quickly.

Features
-------------
Out of the box, HubCommander has the following GitHub features:
* Repository creation
* Repository description and website modification
* Granting outside collaborators specific permissions to repositories
* Repository default branch modification

HubCommander also features the ability to:
* Enable Travis CI on a GitHub repo
* Safeguard commands with 2FA via Duo

You can add additional commands by creating plugins. For example, you can create a plugin to invite users 
to your organizations.

Installation Documentation
-----------
Please see the documentation [here](docs/installation.md) for details.
