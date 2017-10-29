"""
.. module: hubcommander.command_plugins.repeat
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
.. moduleauthor:: Duncan Godfrey @duncangodfrey
"""
from hubcommander.bot_components.decorators import hubcommander_command
from hubcommander.bot_components.bot_classes import BotCommander
from hubcommander.bot_components.slack_comm import send_info

from .config import USER_COMMAND_DICT


class RepeatPlugin(BotCommander):
    def __init__(self):
        super().__init__()

        self.commands = {
            "!Repeat": {
                "command": "!Repeat",
                "func": self.repeat_command,
                "help": "Just repeats text passed in (for testing and debugging purposes)",
                "user_data_required": True,
                "enabled": True
            }
        }

    def setup(self, *args):
        # Add user-configurable arguments to the command_plugins dictionary:
        for cmd, keys in USER_COMMAND_DICT.items():
            self.commands[cmd].update(keys)

    @hubcommander_command(
        name="!Repeat",
        usage="!Repeat <TextToRepeat>",
        description="Text to repeat to test if HubCommander is working.",
        required=[
            dict(name="text", properties=dict(type=str, help="Text to repeat.")),
        ]
    )
    def repeat_command(self, data, user_data, text):
        new_text = data['text'].split(' ', 1)[1]
        send_info(data["channel"], new_text, markdown=True, ephemeral=True, ephemeral_user=user_data["id"])
