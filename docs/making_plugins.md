Making Custom Plugins
=====================

There are two types of plugins that can be created for HubCommander: authentication plugins, and 
command plugins. 

All plugins must be classes, and must implement a `setup()` method that takes in as parameters
a `secrets`, and optional `kwargs`. This is used to pass secrets and other configuration
details to the plugin so that it is ready to use when commands are to be executed.

Authentication Plugins
----------------------
Authentication plugins provide a means of safeguarding commands and providing a speedbump for their
execution.

An example plugin is provided for organizations making use of Duo. Please use the 
[Duo plugin](https://github.com/Netflix/hubcommander/blob/master/auth_plugins/duo/plugin.py) 
as a reference for creating auth plugins.

All auth plugins are child classes of 
[`BotAuthPlugin`](https://github.com/Netflix/hubcommander/blob/master/bot_components/bot_classes.py#L25).

The plugin must implement the `authenticate` method with the following parameters: `data, user_data, **kwargs`, and 
it must return a boolean to indicate if it was successful or not. `True` means that the authentication
was successful, `False` otherwise. Commands that require authentication will continue execution 
if auth was successful, and will stop if there was a failure.

### Enabling Auth Plugins
Please see the [authentication plugins documentation](authentication.md) for details.

Command Plugins
---------------
Command plugins are where you will add custom commands. All command plugins are child classes of 
[`BotCommander`](https://github.com/Netflix/hubcommander/blob/master/bot_components/bot_classes.py#L19).

Please review existing plugins for ideas on how to add plugins to HubCommander. However, to summarize,
you must add a `self.commands = []` with a list of `dict`s to outline the commands that the plugin supports. 
For details on how this should look, please refer to the [command configuration documentation](command_config.md).

Your plugin should have a `config.py` with a `USER_COMMAND_DICT` to permit customization, such as 
the ability to enable authentication and disable a command. To make the custom config stick, you
need the following code in your `setup()` method:
```
    # Add user-configurable arguments to the command_plugins dictionary:
    for cmd, keys in USER_COMMAND_DICT.items():
        self.commands[cmd].update(keys)
```

For command parsing, please take a look at the GitHub plugin for an example for how
that should be done. All existing plugins are making use of `argparse` with some
`try`-`except` logic to handle errors, and to be able to print help text.

### Command Methods
Decorators are provided to perform a lot of the heavy lifting for command functions. All command functions should be
decorated with `@hubcommander_command()`, and `@auth()`.  The first decorator performs the argument parsing and other
pre-command validation, the second enables authentication support for the command. Once the arguments are successfully parsed,
they are then passed into the command function.

More details on how the decorators are used are [documented here](decorators.md).

The command methods take in the following parameters: `data`, if `user_data_required`, then `user_data`, as well as
the remaining parameters defined in `@hubcommander_command`. `data` contains information about the message that arrived,
including the channel that originated the message. `data["channel"]` contains the channel for where the message was posted.

`user_data` contains information about the Slack user that issued the command.
`user_data["name"]` is the Slack username of the user that can be used for `@` mentions.

### Printing Messages
There are three functions provided for convenience when wanting to write to the Slack channel.
They are defined in [`bot_components/slack_comm.py`](https://github.com/Netflix/hubcommander/blob/master/bot_components/slack_comm.py).

Please use the `send_info`, `send_error`, and `send_success` functions to sent info, error, and success messages,
respectively.

These functions take in as parameters the Slack channel to post to (from `data["channel"]` in your command method),
the `text you want to be displayed in the channel`, and whether or not `markdown` should be rendered.

These functions also support threads and ephemeral messages.

#### Threads
For sending messages within Slack threads, Slack requires a timestamp to be sent over. HubCommander provides this in the
`data` dictionary's `ts` value that gets passed into each command function. To use this, in your `send_*` function call, simply
pass in `thread=data["ts"]`. An example of this in action is [here](https://github.com/Netflix/hubcommander/blob/develop/command_plugins/repeat/plugin.py#L65).

#### Ephemeral Messages
Sending ephemeral messages is similar to threads. For this, your command must receive the `user_data` dictionary that gets passed into
each command function. To send the ephemeral message to the user, you need to pass into the `send_*` function call
`ephemeral_user=user_data["id"]`. An example of this in action is [here](https://github.com/Netflix/hubcommander/blob/develop/command_plugins/repeat/plugin.py#L53).


### Add Command Authentication
To add authentication, you simply decorate the method with `@auth` (after the `@hubcommander_command()` decorator)

See the [authentication plugin documentation](authentication.md) for how to enable authentication.

### Enabling Command Plugins
To enable the plugin, you must `import` the plugin's `class` in
[`command_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/command_plugins/enabled_plugins.py)

Then, add an entry to the `COMMAND_PLUGINS` dict with the plugin instantiated. The plugin will get recognized
on startup of the bot and configured.
