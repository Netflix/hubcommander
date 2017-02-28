"""
.. module: hubcommander
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from rtmbot.core import Plugin

from hubcommander.auth_plugins.enabled_plugins import AUTH_PLUGINS
from hubcommander.bot_components.slack_comm import get_user_data, send_error, send_info
from hubcommander.command_plugins.enabled_plugins import GITHUB_PLUGIN, COMMAND_PLUGINS
from hubcommander.config import *
from hubcommander.decrypt_creds import get_credentials

HELP_TEXT = []


def print_help(data):
    text = "I support the following commands:\n"

    for txt in HELP_TEXT:
        text += txt

    text += "`!Help` - This command."
    send_info(data["channel"], text, markdown=True)


COMMANDS = {
    "!help": {"func": print_help, "user_data_required": False}
}


class HubCommander(Plugin):
    def __init__(self, **kwargs):
        super(HubCommander, self).__init__(**kwargs)
        setup(self.slack_client)

    def process_message(self, data):
        """
        The Slack Bot's only required method -- checks if the message involves this bot.
        :param data:
        :return:
        """
        if data["channel"] in IGNORE_ROOMS:
            return

        if len(ONLY_LISTEN) > 0 and data["channel"] not in ONLY_LISTEN:
            return

        # Only process if it starts with one of our GitHub commands:
        command_prefix = data["text"].split(" ")[0].lower()
        if COMMANDS.get(command_prefix):
            process_the_command(data, command_prefix)


def process_the_command(data, command_prefix):
    """
    Will perform all command_plugins duties if a command_plugins arrived.

    :param data:
    :param command_prefix:
    :return:
    """
    # Reach out to slack to get the user's information:
    user_data, error = get_user_data(data)
    if error:
        send_error(data["channel"], "ERROR: Unable to communicate with the Slack API. Error:\n{}".format(error))
        return

    # Execute the message:
    if COMMANDS[command_prefix]["user_data_required"]:
        COMMANDS[command_prefix]["func"](data, user_data)

    else:
        COMMANDS[command_prefix]["func"](data)


def setup(slackclient):
    """
    This is called by the Slack RTM Bot to initialize the plugin.

    This contains code to load all the secrets that are used by all the other services.
    :return:
    """
    # Need to open the secrets file:
    secrets = get_credentials()

    from . import bot_components
    bot_components.SLACK_CLIENT = slackclient

    print("[-->] Enabling Auth Plugins")
    for name, plugin in AUTH_PLUGINS.items():
        print("\t[ ] Enabling Auth Plugin: {}".format(name))
        plugin.setup(secrets)
        print("\t[+] Successfully enabled auth plugin \"{}\"".format(name))
    print("[✔] Completed enabling auth plugins plugins.")

    print("[-->] Enabling Command Plugins")

    # Register the commands for the github plugin first and foremost:
    print("[ ] Enabling github Plugin...")
    GITHUB_PLUGIN.setup(secrets)
    for cmd in GITHUB_PLUGIN.commands.values():
        if cmd["enabled"]:
            COMMANDS[cmd["command"].lower()] = cmd
            print("\t[+] Adding command: \'{cmd}\'".format(cmd=cmd["command"]))
            HELP_TEXT.append("`{cmd}` - {help}\n".format(cmd=cmd["command"], help=cmd["help"]))
        else:
            print("\t[/] Skipping disabled command: \'{cmd}\'".format(cmd=cmd["command"]))
    print("[+] Successfully enabled github plugin.")

    # Register the rest of the command_plugins plugins:
    for name, plugin in COMMAND_PLUGINS.items():
        print("[ ] Enabling Command Plugin: {}".format(name))
        plugin.setup(secrets)
        for cmd in plugin.commands.values():
            if cmd["enabled"]:
                print("\t[+] Adding command: \'{cmd}\'".format(cmd=cmd["command"]))
                COMMANDS[cmd["command"].lower()] = cmd
                HELP_TEXT.append("`{cmd}` - {help}\n".format(cmd=cmd["command"], help=cmd["help"]))
            else:
                print("\t[/] Skipping disabled command: \'{cmd}\'".format(cmd=cmd["command"]))
        print("[+] Successfully enabled command_plugins plugin \"{}\"".format(name))

    print("[✔] Completed enabling command_plugins plugins.")
