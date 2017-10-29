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


def say(channel, attachments, text=None, ephemeral_user=None, thread=None):
    """
    Sends a message (with attachments) to Slack. Use the send_* methods instead.
    :param channel:
    :param attachments:
    :param text:
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :param thread:
    :return:
    """
    kwargs_to_send = {
        "channel": channel,
        "text": text if text else " ",
        "attachments": json.dumps(attachments),
        "as_user": True
    }
    verb = "chat.postMessage"

    if ephemeral_user:
        kwargs_to_send["user"] = ephemeral_user
        verb = "chat.postEphemeral"

    if thread:
        kwargs_to_send["thread_ts"] = thread

    bot_components.SLACK_CLIENT.api_call(verb, **kwargs_to_send)


def send_error(channel, text, markdown=False, ephemeral_user=None, thread=None):
    """
    Sends an "error" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :param thread:
    :return:
    """
    attachment = {
        "text": text,
        "color": "danger",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral_user=ephemeral_user, thread=thread)


def send_info(channel, text, markdown=False, ephemeral_user=None, thread=None):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :param thread:
    :return:
    """
    attachment = {
        "text": text,
        "color": WORKING_COLOR,
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral_user=ephemeral_user, thread=thread)


def send_success(channel, text, markdown=False, ephemeral_user=None, thread=None):
    """
    Sends an "success" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :param thread:
    :return:
    """
    attachment = {
        "text": text,
        "color": "good",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment], ephemeral_user=ephemeral_user, thread=thread)


def send_raw(channel, text, ephemeral_user=None, thread=None):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :param ephemeral_user:ID of the user who will receive the ephemeral message
    :param thread:
    :return:
    """

    say(channel, None, text, ephemeral_user=ephemeral_user, thread=thread)


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
