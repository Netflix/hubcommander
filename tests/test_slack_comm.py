"""
.. module: hubcommander.tests.test_slack_comm
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json

import pytest


def actually_said(channel, attachments, slack_client):
    slack_client.api_call.assert_called_with("chat.postMessage", channel=channel, text=" ",
                                             attachments=json.dumps(attachments), as_user=True)


def test_say(slack_client):
    from hubcommander.bot_components.slack_comm import say
    attachments = {"attachment_is": "ʕ•ᴥ•ʔ"}

    say("some_channel", attachments)

    actually_said("some_channel", attachments, slack_client)


@pytest.mark.parametrize("markdown", [True, False])
def test_send_error(slack_client, markdown):
    from hubcommander.bot_components.slack_comm import send_error
    attachment = {
        "text": "ʕ•ᴥ•ʔ",
        "color": "danger"
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    send_error("some_channel", attachment["text"], markdown)

    actually_said("some_channel", [attachment], slack_client)


@pytest.mark.parametrize("markdown", [True, False])
def test_send_info(slack_client, markdown):
    from hubcommander.bot_components.slack_comm import send_info, WORKING_COLOR
    attachment = {
        "text": "ʕ•ᴥ•ʔ",
        "color": WORKING_COLOR
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    send_info("some_channel", attachment["text"], markdown)

    actually_said("some_channel", [attachment], slack_client)


@pytest.mark.parametrize("markdown", [True, False])
def test_send_success(slack_client, markdown):
    from hubcommander.bot_components.slack_comm import send_success
    attachment = {
        "text": "ʕ•ᴥ•ʔ",
        "color": "good"
    }

    if markdown:
        attachment["mrkdwn_in"] = ["text"]

    send_success("some_channel", attachment["text"], markdown)

    actually_said("some_channel", [attachment], slack_client)


def test_get_user(slack_client):
    from hubcommander.bot_components.slack_comm import get_user_data
    result, error = get_user_data({"user": "hcommander"})
    assert not error
    assert result["name"] == "hcommander"

    result, error = get_user_data({"user": "error"})
    assert not result
    assert error
