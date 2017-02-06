"""
.. module: hubcommander.bot_components.slack_comm
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json

import bot_components

# A nice color to output
WORKING_COLOR = "#439FE0"


def say(channel, attachments):
    """
    Sends a message (with attachments) to Slack. Use the send_* methods instead.
    :param channel:
    :param attachments:
    :return:
    """
    bot_components.SLACK_CLIENT.api_call("chat.postMessage", channel=channel, text=" ",
                                         attachments=json.dumps(attachments), as_user=True)


def send_error(channel, text, markdown=False):
    """
    Sends an "error" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :return:
    """
    attachment = {
        "text": text,
        "color": "danger",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment])


def send_info(channel, text, markdown=False):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :param markdown: If True, then look for markdown in the message.
    :return:
    """
    attachment = {
        "text": text,
        "color": WORKING_COLOR,
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [
        attachment
    ])


def send_success(channel, text, markdown=False):
    """
    Sends an "success" message to Slack.
    :param channel:
    :param text:
    :param image: A choice of "awesome", "yougotit".
    :param markdown: If True, then look for markdown in the message.
    :return:
    """
    attachment = {
        "text": text,
        "color": "good",
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    say(channel, [attachment])


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


def preformat_args(text):
    return text.lower() \
               .replace('[', '').replace(']', '') \
               .replace('{', '').replace('}', '') \
               .split(" ")[1:]


def preformat_args_with_spaces(text, num_quoted):
    working = text.replace('[', '').replace(']', '') \
        .replace('{', '').replace('}', '') \
        .replace(u'\u201C', "\"").replace(u'\u201D', "\"") \
        .replace(u'\u2018', "\'").replace(u'\u2019', "\'")  # Slack's Bullshit around quotes..

    # Check if there are 0 or an un-even number of quotation marks.  If so, then exit:
    if working.count('\"') < 2:
        raise SystemExit()

    if working.count('\"') % 2 != 0:
        raise SystemExit()

    # Get all the quoted things:
    quotes = working.split('"')[1::2]
    if len(quotes) != num_quoted:
        raise SystemExit()

    # Remove them from the working string:
    working = working.replace("\"", '')

    for quote in quotes:
        working = working.replace(quote, '')

    # Get the space delimited commands:
    working = working.lower()
    space_delimited = working.split(" ")[1:-1]
    # The -1 above is needed, because there will be additional empty items on the list due to the space
    # after the other positional arguments :/

    return space_delimited + quotes


def extract_repo_name(reponame):
    """
    Reponames can be FQDN's. Slack has an annoying habit of sending over URL's like so:
    <http://www.foo.com|www.foo.com>
    ^^ Need to pull out the URL. In our case, we care only about the label, which is the last part between | and >
    :param reponame:
    :return:
    """
    if "|" not in reponame:
        return reponame

    split_repo = reponame.split("|")[1]

    return split_repo.replace(">", "")
