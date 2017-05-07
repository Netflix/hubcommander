"""
.. module: hubcommander.tests.conftest
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from unittest.mock import MagicMock

import pytest
import slackclient
from bot_components.bot_classes import BotAuthPlugin

USER_DATA = {
    "ok": True,
    "user": {
        "profile": {
            "first_name": "Hub",
            "last_name": "Commander",
            "phone": "1112223333",
            "image_1024": "https://some/path.jpg",
            "title": "Awesome",
            "real_name": "HubCommander",
            "image_24": "https://some/path.jpg",
            "image_original": "https://some/path.jpg",
            "real_name_normalized": "HubCommander",
            "image_512": "https://some/path.jpg",
            "image_72": "https://some/path.jpg",
            "image_32": "https://some/path.jpg",
            "image_48": "https://some/path.jpg",
            "skype": "",
            "avatar_hash": "123456789abc",
            "email": "hc@hubcommander",
            "image_192": "https://some/path.jpg"
        },
        "status": None,
        "tz": "America/Los_Angeles",
        "name": "hcommander",
        "deleted": False,
        "is_bot": False,
        "tz_offset": -28800,
        "real_name": "Hub Commander",
        "color": "7d414c",
        "team_id": "T12345678",
        "is_admin": False,
        "is_ultra_restricted": False,
        "is_restricted": False,
        "is_owner": False,
        "tz_label": "Pacific Standard Time",
        "id": "U12345678",
        "is_primary_owner": False
    }
}


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_addoption(parser):
    parser.addoption("--hubcommanderconfig", help="override the default test config")


def slack_client_side_effect(*args, **kwargs):
    if args[0] == "users.info":
        if kwargs["user"] == "error":
            return {"error": "Error"}
        return USER_DATA


@pytest.fixture(scope="function")
def slack_client():
    import hubcommander.bot_components.slack_comm
    sc = slackclient.SlackClient("testtoken")
    sc.api_call = MagicMock(side_effect=slack_client_side_effect)

    # Need to fix both:
    hubcommander.bot_components.SLACK_CLIENT = sc
    hubcommander.bot_components.slack_comm.bot_components.SLACK_CLIENT = sc

    return sc


@pytest.fixture(scope="function")
def user_data(slack_client):
    import hubcommander.bot_components.slack_comm
    hubcommander.bot_components.slack_comm.bot_components.SLACK_CLIENT = slack_client

    from bot_components.slack_comm import get_user_data
    return get_user_data(USER_DATA)[0]


@pytest.fixture(scope="function")
def auth_plugin():
    class TestAuthPlugin(BotAuthPlugin):
        def __init__(self):
            super().__init__()

        def authenticate(self, data, user_data, should_auth=False):
            return should_auth

    return TestAuthPlugin()
