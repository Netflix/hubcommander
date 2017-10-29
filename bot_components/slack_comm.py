"""
.. module: hubcommander.bot_components.slack_comm
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json

from hubcommander import bot_components

# A nice color to output
WORKING_COLOR = "#439FE0"


def say(channel, attachments, text=None, ephemeral=False, ephemeral_user=None):
    """
    Sends a message (with attachments) to Slack. Use the send_* methods instead.
    :param channel:
    :param attachments:
    :param text:
    :param ephemeral: If True, then send send ephemeral message
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :return:
    """
    if text is None:
        text = " "

    if ephemeral:
        bot_components.SLACK_CLIENT.api_call("chat.postEphemeral",
                                             channel=channel, text=text,
                                             user=ephemeral_user,
                                             attachments=json.dumps(attachments),
                                             as_user=True)
    else:
        bot_components.SLACK_CLIENT.api_call("chat.postMessage",
                                             channel=channel, text=text,
                                             attachments=json.dumps(attachments),
                                             as_user=True)


def send_error(channel, text, markdown=False, ephemeral=False,
               ephemeral_user=None):
    """
    Sends an "error" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral: True to send ephemeral mesaage
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :return:
    """
    attachment = {
        "text": text,
        "color": "danger",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral=ephemeral,
        ephemeral_user=ephemeral_user)


def send_info(channel, text, markdown=False, ephemeral=False,
              ephemeral_user=None):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral: True to send ephemeral mesaage
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :return:
    """
    attachment = {
        "text": text,
        "color": WORKING_COLOR,
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral=ephemeral,
        ephemeral_user=ephemeral_user)


def send_success(channel, text, markdown=False, ephemeral=False,
                 ephemeral_user=None):
    """
    Sends an "success" message to Slack.
    :param channel:
    :param text:
    :param image: A choice of "awesome", "yougotit".
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral: True to send ephemeral mesaage
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :return:
    """
    attachment = {
        "text": text,
        "color": "good",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral=ephemeral,
        ephemeral_user=ephemeral_user)


def send_raw(channel, text, ephemeral=False, ephemeral_user=None):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :param ephemeral: True to send ephemeral mesaage
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :return:
    """

    say(channel, None, text, ephemeral=ephemeral, ephemeral_user=ephemeral_user)


def get_user_data(data):
    """
    Gets information about the calling user from the Slack API.
    NOTE: Must be called after get_tokens()

    :param data:
    :return:
    """
    result = bot_components.SLACK_CLIENT.api_call("users.info", user=data["user"])
    if result.get("error"):
        return None, result["error"]

    else:
        return result["user"], None

