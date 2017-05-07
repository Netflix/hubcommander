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


def perform_additional_verification(args, **kwargs):
    for at in ARG_TYPE:
        if kwargs.get(at):
            for argument in kwargs[at]:
                if argument.get("validation_func"):
                    validation_kwargs = {}
                    if argument.get("validation_func_kwargs"):
                        validation_kwargs = argument["validation_func_kwargs"]

                    real_arg_name = argument["name"].replace("--", "")
                    args[real_arg_name] = argument["validation_func"](
                        args[real_arg_name], **validation_kwargs
                    )

    return args


def hubcommander_command(**kwargs):
    def command_decorator(func):
        def decorated_command(obj, data, user_data):
            parser = argparse.ArgumentParser(prog=kwargs["name"],
                                             description=kwargs["description"],
                                             usage=kwargs["usage"])

            # Dynamically add in the required and optional arguments:
            arg_type = ["required", "optional"]
            for at in arg_type:
                if kwargs.get(at):
                    for argument in kwargs[at]:
                        parser.add_argument(argument["name"], **argument["properties"])

            # Remove the command from the command string:
            split_args = shlex.split(data["text"])[1:]
            try:
                args = vars(parser.parse_args(split_args))

            except SystemExit as _:
                send_info(data["channel"], format_help_text(data, user_data, **kwargs), markdown=True)
                return

            # Perform additional verification:
            try:
                args = perform_additional_verification(args, **kwargs)
            except ParseException as pe:
                send_error(data["channel"], pe.format_proper_usage(user_data["name"]),
                           markdown=True)
                return

            # Run the next function:
            data["command_name"] = kwargs["name"]
            return func(obj, data, user_data, **args)

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
