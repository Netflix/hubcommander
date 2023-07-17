"""
.. module: hubcommander.bot_components.decorators
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import argparse
import shlex

from hubcommander.bot_components.parse_functions import ParseException
from hubcommander.bot_components.slack_comm import send_info, send_error

ARG_TYPE = ["required", "optional"]


def format_help_text(data, user_data, **kwargs):
    full_help_text = "@{user}: `{command_name}`: {description}\n\n" \
                     "```{usage}```\n\n" \
                     "{required}" \
                     "{optional}"

    required_args = []
    if kwargs.get("required"):
        required_args.append("Required Arguments:")
        for required in kwargs["required"]:
            if type(required["name"]) is list:
                required_args.append("\t`{name}`\t{help}".format(name=", ".join(required["name"]),
                                                                 help=required["properties"]["help"]))
            else:
                required_args.append("\t`{name}`\t{help}".format(name=required["name"],
                                                                 help=required["properties"]["help"]))

        required_args = "\n".join(required_args) + "\n\n"

    optional_args = ["Optional Arguments:",
                     "\t`-h, --help`\tShow this help text."]
    if kwargs.get("optional"):
        for optional in kwargs["optional"]:
            if type(optional["name"]) is list:
                optional_args.append("\t`{name}`\t{help}".format(name=", ".join(optional["name"]),
                                                                 help=optional["properties"]["help"]))
            else:
                optional_args.append("\t`{name}`\t{help}".format(name=optional["name"],
                                                                 help=optional["properties"]["help"]))

    optional_args = "\n".join(optional_args)

    return full_help_text.format(
        user=user_data["name"],
        command_name=kwargs["name"],
        description=kwargs["description"],
        usage=kwargs["usage"],
        required=required_args if required_args else "",
        optional=optional_args if optional_args else ""
    )


def perform_additional_verification(plugin_obj, args, **kwargs):
    """
    This will run the custom verification functions that you can set for parameters.

    This will also, by default, lowercase all values that arrive. This behavior can be disabled
    via the lowercase=False flag for the argument.
    :param plugin_obj:
    :param args:
    :param kwargs:
    :return:
    """
    for at in ARG_TYPE:
        if kwargs.get(at):
            for argument in kwargs[at]:
                # Perform case changing logic if required (lowercase by default)
                real_arg_name = argument["name"].replace("--", "")
                if args.get(real_arg_name):
                    if type(args[real_arg_name]) is str:
                        if argument.get("uppercase", False):
                            args[real_arg_name] = args[real_arg_name].upper()

                        elif argument.get("lowercase", True):
                            args[real_arg_name] = args[real_arg_name].lower()

                        # Perform cleanups? Removes <>, {}, &lt;&gt; from the variables if `cleanup=False` not set.
                        if argument.get("cleanup", True):
                            args[real_arg_name] = args[real_arg_name].replace("<", "") \
                                .replace(">", "").replace("{", "").replace("}", "") \
                                .replace("[", "").replace("]", "") \
                                .replace("&lt;", "").replace("&gt;", "")

                    # Perform custom validation if needed:
                    if argument.get("validation_func"):
                        validation_kwargs = {}
                        if argument.get("validation_func_kwargs"):
                            validation_kwargs = argument["validation_func_kwargs"]

                        args[real_arg_name] = argument["validation_func"](
                            plugin_obj, args[real_arg_name], **validation_kwargs
                        )

    return args


def hubcommander_command(**kwargs):
    def command_decorator(func):
        def decorated_command(plugin_obj, data, user_data):
            parser = argparse.ArgumentParser(prog=kwargs["name"],
                                             description=kwargs["description"],
                                             usage=kwargs["usage"])

            # Add the optional auth_token parameter to all commands
            parser.add_argument("--auth_token", type=str, help="Optional authentication token that can be specified ")

            # Dynamically add in the required and optional arguments:
            arg_type = ["required", "optional"]
            for at in arg_type:
                if kwargs.get(at):
                    for argument in kwargs[at]:
                        # If there is a list of available values, then ensure that they are added in for argparse to
                        # process properly. This can be done 1 of two ways:
                        #  1.) [Not recommended] Use argparse directly by passing in a fixed list within
                        #       `properties["choices"]`
                        #
                        #  2.) [Recommended] Add `choices` outside of `properties` where you can define where
                        #      the list of values appear within the Plugin's command config. This is
                        #      preferred, because it reflects how the command is actually configured after the plugin's
                        #      `setup()` method is run.
                        #
                        #      To make use of this properly, you need to have the help text contain: "{values}"
                        #      This will then ensure that the list of values are properly in there.
                        ##
                        if argument.get("choices"):
                            # Add the dynamic choices:
                            argument["properties"]["choices"] = plugin_obj.commands[kwargs["name"]][argument["choices"]]

                            # Fix the help text:
                            argument["properties"]["help"] = argument["properties"]["help"].format(
                                values=", ".join(plugin_obj.commands[kwargs["name"]][argument["choices"]])
                            )

                        parser.add_argument(argument["name"], **argument["properties"])

            # Remove all the macOS "Smart Quotes":
            data["text"] = data["text"].replace(u'\u201C', "\"").replace(u'\u201D', "\"") \
                .replace(u'\u2018', "\'").replace(u'\u2019', "\'")

            # Remove the command from the command string:
            split_args = shlex.split(data["text"])[1:]
            try:
                args = vars(parser.parse_args(split_args))

            except SystemExit as _:
                send_info(data["channel"], format_help_text(data, user_data, **kwargs), markdown=True,
                          ephemeral_user=user_data["id"])
                return

            # Perform additional verification:
            try:
                args = perform_additional_verification(plugin_obj, args, **kwargs)
            except ParseException as pe:
                send_error(data["channel"], pe.format_proper_usage(user_data["name"]),
                           markdown=True, ephemeral_user=user_data["id"])
                return
            except Exception as e:
                send_error(data["channel"], "An exception was encountered while running validation for the input. "
                                            "The exception details are: `{}`".format(str(e)),
                           markdown=True)
                return

            # Run the next function:
            data["command_name"] = kwargs["name"]
            # If an auth token was specified, move it from the args array to the data dict, visible to auth plugins
            if 'auth_token' in args:
                data['auth_token'] = args['auth_token']
                del args['auth_token']
            return func(plugin_obj, data, user_data, **args)

        return decorated_command

    return command_decorator


def auth(**kwargs):
    def command_decorator(func):
        def decorated_command(command_plugin, data, user_data, *args, **kwargs):
            # Perform authentication:
            if command_plugin.commands[data["command_name"]].get("auth"):
                if not command_plugin.commands[data["command_name"]]["auth"]["plugin"].authenticate(
                        data, user_data, *args, **command_plugin.commands[data["command_name"]]["auth"]["kwargs"]):
                    return

            # Run the next function:
            return func(command_plugin, data, user_data, *args, **kwargs)

        return decorated_command

    return command_decorator
