Authentication Plugins
===================
HubCommander supports the ability to add authentication to the command flow. This is useful to safeguard
specific commands, and additionally, add a speedbump to privileged commands.

For organizations making use of Duo, a plugin is supplied that will prompt a user's device for approval
before a command is executed.

Making Auth Plugins
-------------
See the documentation for creating Auth plugins
[here](https://github.com/Netflix/hubcommander/blob/master/docs/making_plugins.md#authentication-plugins).

Enabling Auth Plugins
--------------
You first need to `import` the authentication plugin in the 
[`auth_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/auth_plugins/enabled_plugins.py) 
file. Then, you need to instantiate the plugin in the `AUTH_PLUGINS` `dict`.

Once the plugin is enabled, you then need to modify a plugin's given command to make use of the specific authentication
plugin. This is done by adding a command specific configuration entry to the `USER_COMMAND_DICT`.
An example for how this is configured can be found in 
[`github/config.py`](https://github.com/Netflix/hubcommander/blob/master/github/config.py).

Enabling Duo
------------
Duo is disabled by default. To enable Duo, you will need the following information:
   1. The domain name that is Duo protected
   1. The Duo Host
   1. The "IKEY"
   1. The "SKEY"

HubCommander supports multiple Duo domains. For this to work, you will need the information above
for the given domain. Additionally, the secrets dictionary needs to be updated such that it has a key that starts
with `DUO_`.  This key needs a comma-separated list of the domain, duo host, `ikey`, and `skey`.  It needs to look like:

    "DUO_DOMAIN_ONE": "domainone.com,YOURHOST.duosecurity.com,THEIKEY,THESKEY"
    "DUO_DOMAIN_TWO": "domaintwo.com,YOUROTHERHOST.duosecurity.com,THEOTHERIKEY,THEOTHERSKEY"

The email address of the Slack user will determine which domain gets used.

With the above information, you need to modify the secrets `dict` that is decrypted by the application
on startup.

Additionally, you will need to uncomment out the `import` statement in 
[`auth_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/auth_plugins/enabled_plugins.py),
and also uncomment the `"duo": DuoPlugin()` entry in `AUTH_PLUGINS`.

Using Authentication for Custom Commands
---------
You need to decorate methods with `@hubcommander_command`, and `@auth`. Please refer to the
[making plugins](making_plugins.md) documentation for details.
