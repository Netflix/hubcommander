Authentication Plugins
===================
HubCommander supports the ability to add authentication to the command flow. This is useful to safegurad
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

   - `DUO-HOST`: Your administrator needs to provide you with this
   - `DUO-IKEY`: The `IKEY`, provided to you by your administrator
   - `DUO-SKEY`: The `SKEY`, provided to you by your administrator

With the above information, you need to modify the secrets `dict` that is decrypted by the application
on startup.

Additionally, you will need to uncomment out the `import` statement in 
[`auth_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/auth_plugins/enabled_plugins.py),
and also uncomment the `"duo": DuoPlugin()` entry in `AUTH_PLUGINS`.
