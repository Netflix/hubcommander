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


def test_preformat_args():
    from hubcommander.bot_components.slack_comm import preformat_args
    test_string = "!TheCommand [argOne] {argTwo}"
    result = preformat_args(test_string)
    assert len(result) == 2
    assert result[0] == "argone"
    assert result[1] == "argtwo"


def test_preformat_args_with_spaces():
    from hubcommander.bot_components.slack_comm import preformat_args_with_spaces
    test_string = "!TheCommand [argOne] {argTwo} “argThree” \"argFour\" \"argFive\""
    result = preformat_args_with_spaces(test_string, 3)
    assert len(result) == 5
    assert result[0] == "argone"
    assert result[1] == "argtwo"
    assert result[2] == "argThree"
    assert result[3] == "argFour"
    assert result[4] == "argFive"

    test_string_two = "!SetDescription Netflix HubCommander \"A Slack bot for GitHub ‘management’\""
    result = preformat_args_with_spaces(test_string_two, 1)
    assert len(result) == 3
    assert result[2] == "A Slack bot for GitHub 'management'"

    test_failures = [
        "!SomeCommand \"only one quote",
        "!SomeCommand \"three quotes\"\"",
        "!SomeCommand no quotes",
    ]
    for tf in test_failures:
        with pytest.raises(SystemExit):
            preformat_args_with_spaces(tf, 1)

    # Failure with incorrect number of quoted params:
    with pytest.raises(SystemExit):
        preformat_args_with_spaces(test_string_two, 3)


def test_extract_repo_name():
    from hubcommander.bot_components.slack_comm import extract_repo_name
    test_strings = {
        "www.foo.com": "<http://www.foo.com|www.foo.com>",
        "foo": "foo",
        "HubCommander": "HubCommander",
        "netflix.github.com": "<https://netflix.github.com|netflix.github.com>"
    }

    for repo, uri in test_strings.items():
        assert extract_repo_name(uri) == repo
