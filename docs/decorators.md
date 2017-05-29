Command Decorators & Argument Parsing
===================
HubCommander features decorators that can perform the heavy lifting of argument parsing, as well as performing
pre-command validation, and authentication.

Declaring HubCommander Commands
-------------
The primary decorator that must be placed on all HubCommander commands is `@hubcommander_command`. This decorator
does all of the argument parsing, and provides mechanisms where you can define your own custom parsers.

Here is an example:
```
    @hubcommander_command(
        name="!SetBranchProtection",
        usage="!SetBranchProtection <OrgThatHasRepo> <Repo> <BranchName> <On|Off>",
        description="This will enable basic branch protection to a GitHub repo.\n\n"
                    "Please Note: GitHub prefers lowercase branch names. You may encounter issues "
                    "with uppercase letters.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to set the default on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="branch", properties=dict(type=str, help="The name of the branch to set as default. "
                                                               "(Case-Sensitive)"), lowercase=False),
            dict(name="toggle", properties=dict(type=str, help="Toggle to enable or disable branch protection"),
                 validation_func=parse_toggles, validation_func_kwargs={})
        ],
        optional=[]
    )
```

Here are the components:
- `name`: This is the command itself. This must be defined in the plugin's `commands` `dict`.
- `usage`: This is the command usage help text. This should be a simple summary of the command and its arguments.
- `description`: A description of what the command does. Make this as detailed as you need it to be.
- `required`: This is a list (order matters) of the arguments that are required for the command to execute properly.
- `optional`: Similar to `required`, this is a list of optional arguments that can be supplied to the command.

### Argument Parsing
Argument parsing is handled by Python's [`argparse`](https://docs.python.org/3/library/argparse.html) library.
The `@hubcommander_command` decorator provides some higher-level wrapping logic around it.

To make use of HubCommander's argument parsing, you need to define a list of `dict`s under `required` or `optional`
that have the following fields:
- `name`: **-Required-** The name of the argument
- `properties`: **-Required-** This is what actually gets passed into `argparse`. The main elements here that you need to be concerned with are:
  - `type`: **-Required-** The Python type of the argument. This will typically be `str` (recommended), but can also be `int` or any other Python type.
  - `help`: **-Required-** This is the text that will appear for the given argument in the usage output. Make this descriptive to what the argument is.
- `lowercase`: This is `True` by **default** for all `str` arguments. This will lowercase the argument. If you have case-sensitive arguments, set this to `False`.
- `uppercase`: `False` by default for all `str` arguments. This will uppercase the argument if set to `True`.
- `cleanup`: This is `True` by **default** for all `str` arguments. This will remove brackets `<>, {}, []` and replace macOS "smart quotes" with regular quotation characters.
- `validation_func`: This is the Python function that will perform additional validation and transformation against the argument beyond what `argparse` can do. This is detailed further below.
- `validation_func_kwargs`: A `dict` containing the keyword arguments to pass into the validation function defined above.
- `choices`: This is used when there is a specific list fo values that are acceptable for the command. This field is supposed to be used
   in conjunction with the plugin's `commands` `dict`. This contains the name of the list with the acceptable values, and passes that
   into `argparse`. This will also properly format the help text. This is also further detailed below.


#### Validation Functions
Validation functions provide additional validation and transformation that is not possible to perform with `argparse`.

As an example, a validation function is provided that can parse common toggle types, such as `off`, `on`, `true`, `false`, `enabled`, and `disabled`.
To make use of this, you would define an argument that has the `parse_toggles` function set. Here is an example:
```
    dict(name="toggle", properties=dict(type=str, help="Toggle to enable or disable branch protection"),
         validation_func=parse_toggles, validation_func_kwargs={})
```
This will verify that the input for the `toggle` argument will fit the one of the acceptable values for that field.
If the value is an enabling toggle, the function will return `True`, or return `False` if it's a disabling toggle.

However, if the toggle is invalid, the method will raise a `ParseException`. This will be caught in the `@hubcommander_command` decorator.
This will cause HubCommander to output details about what the acceptable values are. This output is set by passing in the usage text to the exception.

To make your own, use the pre-existing ones as an example. You can find examples of these in `bot_components/parse_functions.py`,
and you can also reference `command_plugins/github/parse_functions.py` as well.


#### Multiple choices/options
Python's `argparse` supports the ability of specifying lists. You can certainly have that defined
in the `properties` `dict`, however, this does no permit configurability. With HubCommander, it
is designed so that a plugin's configuration file can outline overridable parameters. As such,
it is recommended to avoid directly specifying the options in the decorator.

Instead, `@hubcommander_command` has an abstraction layer that can take care of that for you.

Here is an example of a multiple choice argument, as seen in the `!ListPRs` command:
```
    dict(name="state", properties=dict(type=str, help="The state of the PR. Must be one of: `{values}`"),
         choices="permitted_states")
```

In here, `choices` refers to the name of the `plugin.commands[THECOMMANDHERE][AListOfAvailableChoices]`. It is the name
of the `list` within the plugin's command configuration that contains the available choices for the argument. This is done
because it allows the user of HubCommander to override this list in the plugin's configuration.

Additionally, the `help` text is altered to include `{values}`. The `@hubcommander_command` decorator will properly format
the help text for that argument and fill in `{values}` with a comma separated list of the values in the specified list.

In the example above, `permitted_states` is found in the GitHub `!ListPrs` command config, which looks like this:
```
class GitHubPlugin(BotCommander):
    def __init__(self):
        super().__init__()

        self.commands = {
            ...
            "!ListPRs": {
                "command": "!ListPRs",
                "func": self.list_pull_requests_command,
                "user_data_required": True,
                "help": "List the Pull Requests for a repo.",
                "permitted_states": ["open", "closed", "all"],  # <-- This is what "choices" refers to.
                "enabled": True
            },
            ...
        }
        ...
```
The help text will be formatted to say ``The state of the PR. Must be one of: `open, closed, all` ``.

#### Access to the plugin object
Both validation functions and decorators take in the plugin object as the first parameter. This is useful
as it allows you to access all of the attributes, configuration, and functions that are a part of the
plugin.

An example of this is in the GitHub plugin. There are decorators that will verify that
repositories exist. These decorators utilize the GitHub plugin's configuration to access
the GitHub API, and verify that the repository exists before the command function is executed.

## Authentication
To add authentication support, you simply add the `@auth()` decorator after the `@hubcommander_command` decorator.

Custom Decorators
-------------
Feel free to add custom decorators as you like. In general, plugin specific decorators should reside within the
the directory of the plugin. For convention, we use `decorators.py` as the filename for decorators, and
`parse_functions.py` for verification functions.

Please refer to the existing plugins for ideas on how to implement and expand these.

Of course, please feel free to submit pull requests with new decorators and verification functions!
