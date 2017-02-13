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


def say(channel, attachments, text=None):
    """
    Sends a message (with attachments) to Slack. Use the send_* methods instead.
    :param channel:
    :param attachments:
    :param raw:
    :return:
    """
    if text is None:
        bot_components.SLACK_CLIENT.api_call("chat.postMessage", channel=channel, text=" ",
                                             attachments=json.dumps(attachments), as_user=True)
    else:
        bot_components.SLACK_CLIENT.api_call("chat.postMessage", channel=channel, text=text,
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

    say(channel, [attachment])


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

def send_raw(channel, text):
    """
    Sends an "info" message to Slack.
    :param channel:
    :param text:
    :return:
    """

    say(channel, None, text)

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
    """
    This method will not only strip out the things that need to be stripped out, but it will also
    ensure that double-quoted objects are extracted as independent arguments.

    For example, if the text passed in was:
    !SetDescription Netflix HubCommander "A Slack bot for GitHub management", we would want to get back:
    a list that contains: ["netflix", "hubcommander", '"A Slack bot for GitHub management"']

    The `num_quoted` param refers to the number of double-quoted parameters are required for the command.
    For the example above, there is one double-quoted parameter required for the command.

    :param text:
    :param num_quoted:
    :return:
    """
    working = text.replace('[', '').replace(']', '') \
        .replace('{', '').replace('}', '') \
        .replace(u'\u201C', "\"").replace(u'\u201D', "\"") \
        .replace(u'\u2018', "\'").replace(u'\u2019', "\'")  # macOS's Bullshit around quotes..

    # Check if there are 0 or an un-even number of quotation marks.  If so, then exit:
    if working.count('\"') < 2:
        raise SystemExit()

    if working.count('\"') % 2 != 0:
        raise SystemExit()

    # Get all the quoted things: (We only really care about the double-quotes, since they are related to command
    # syntax.)
    quotes = working.split('"')[1::2]
    if len(quotes) != num_quoted:
        raise SystemExit()

    # Remove them from the working string:
    working = working.replace("\"", '')

    for quote in quotes:
        working = working.replace(quote, '')

    # Get the space delimited commands:
    working = working.lower()

    # Remove extra dangling whitespaces (there must be 1 dangling space at the end for the split operation to operate):
    if num_quoted > 1:
        working = working[0:-(num_quoted - 1)]

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
