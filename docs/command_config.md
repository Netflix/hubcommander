Command Configuration
====================
Commands in HubCommander are setup in such a way that they can be modified.

All plugins in HubCommander expose commands via a `dict`. For example, 
see the [`github/plugin.py`](https://github.com/Netflix/hubcommander/blob/master/github/plugin.py#L23)'s 
`init()` method.

In there, there is a `self.commands = {}`. The `dict` entry is the case-sensitive command with a nested `dict` with the
command configuration. At a minimum, each command has the following fields:

   - `command`: The specific command (ALWAYS prefixed with `!`). This is the **SAME** as the dict entry name.
                This is case sensitive for the dict, but the command itself that the user executes is not 
                case sensitive. 
   - `help`: This is the help text for the command that will be output when running
             the `!help` command.
   - `user_data_required`: This should generally be set to `True`. This means that the function
                           will reference the user that sent the command in (like for `@` mentions).
   - `enabled`: Either `True` or `False`. Disabled commands will not be reachable.
   - `func`: This is the actual function that will be run to process the command.
   
Additional Configuration
------------------------
Commands can have additional configuration to disable commands and to enable authentication for them.

In the plugin's respective `config.py` file, there is a `dict` named `USER_COMMAND_DICT`. This dictionary is
merged with the plugin's commands in the `setup()` method on startup. This is where you will make command-specific
configuration settings.

### Disabling Commands
By default, all commands are enabled. To disable a command, you need to add an `enabled: False` to the
`USER_COMMAND_DICT`'s entry for the command. For example to disable the ability to create new repositories,
you would set the GitHub plugin's `USER_COMMAND_DICT` to contain:
```
USER_COMMAND_DICT = {
 "!CreateRepo": {
     "enabled": False
 }
}
```

### Enabling Authentication
By default, authentication is disabled. An example of enabling authentication can be see in the GitHub plugin's
[`config.py`](https://github.com/Netflix/hubcommander/blob/master/github/config.py) file.

_For more details on authentication plugins, please read the [authentication plugin documentation](authentication.md)._
