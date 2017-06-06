"""
.. module: hubcommander.command_plugins.travis_ci.plugin
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json
import time

import requests

from hubcommander.bot_components.bot_classes import BotCommander
from hubcommander.bot_components.decorators import hubcommander_command, auth
from hubcommander.bot_components.slack_comm import send_error, send_info, send_success
from hubcommander.bot_components.parse_functions import extract_repo_name, ParseException

from tabulate import tabulate

from .config import USER_COMMAND_DICT, USER_AGENT, ORGS


TRAVIS_URLS = {
    "pro": "https://api.travis-ci.com",
    "public": "https://api.travis-ci.org"
}


class TravisCIException(Exception):
    pass


def lookup_real_org(plugin_obj, org, **kwargs):
    try:
        return plugin_obj.org_lookup[org.lower()][0]
    except KeyError as _:
        raise ParseException("org", "Either that org doesn't exist, or Travis CI is not enabled for it."
                                    "Run `!ListTravisOrgs` to see which orgs this bot manages.")


class TravisPlugin(BotCommander):
    def __init__(self):
        super().__init__()

        self.commands = {
            "!ListTravisOrgs": {
                "command": "!ListTravisOrgs",
                "func": self.list_org_command,
                "user_data_required": False,
                "help": "Lists the GitHub organizations that have Travis CI enabled.",
                "enabled": True
            },
            "!EnableTravis": {
                "command": "!EnableTravis",
                "func": self.enable_travis_command,
                "help": "Enables Travis CI on a GitHub Repo.",
                "user_data_required": True,
                "enabled": True
            }
        }

        # For org alias lookup convenience:
        self.org_lookup = None

        self.credentials = None

    def setup(self, secrets, **kwargs):
        # GitHub is a dependency:
        from hubcommander.command_plugins.enabled_plugins import COMMAND_PLUGINS
        if not COMMAND_PLUGINS.get("github"):
            self.commands = {}
            print("[X] Travis CI Plugin is not enabling any commands because"
                  " the GitHub plugin is not enabled.")
            return

        # Create the lookup table:
        self.org_lookup = {}
        for org in ORGS.items():
            # The lookup table is the lowercase real name of the org, plus the aliases, along with
            # a tuple containing the full real name of the org, with the org dict details:
            self.org_lookup[org[0].lower()] = (org[0], org[1])
            for alias in org[1]["aliases"]:
                self.org_lookup[alias] = (org[0], org[1])

        self.credentials = {
            "pro": {
                "user": secrets["TRAVIS_PRO_USER"],
                "id": secrets["TRAVIS_PRO_ID"],
                "token": secrets["TRAVIS_PRO_TOKEN"]
            },
            "public": {
                "user": secrets["TRAVIS_PUBLIC_USER"],
                "id": secrets["TRAVIS_PUBLIC_ID"],
                "token": secrets["TRAVIS_PUBLIC_TOKEN"]
            }
        }

        # Add user-configurable arguments to the command_plugins dictionary:
        for cmd, keys in USER_COMMAND_DICT.items():
            self.commands[cmd].update(keys)

    @staticmethod
    def list_org_command(data):
        """
        The "!ListTravisOrgs" command. Lists all organizations that have Travis CI enabled.
        :param data:
        :return:
        """
        headers = ["Alias", "Organization"]
        rows = []
        for org in ORGS.items():
            rows.append([org[0].lower(), org[0]])
            for alias in org[1]["aliases"]:
                rows.append([alias, org[0]])

        send_info(data["channel"], "Travis CI is enabled on the following orgs:\n"
                                   "```{}```".format(tabulate(rows, headers=headers)), markdown=True)

    @hubcommander_command(
        name="!EnableTravis",
        usage="!EnableTravis <OrgWithRepo> <Repo>",
        description="This will enable Travis CI on a GitHub repository.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The repository to enable Travis CI on."),
                 validation_func=extract_repo_name, validation_func_kwargs={})
        ],
        optional=[]
    )
    @auth()
    def enable_travis_command(self, data, user_data, org, repo):
        """
        Enables Travis CI on a repository within the organization.

        Command is as follows: !enabletravis <organization> <repo>
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        from hubcommander.command_plugins.enabled_plugins import COMMAND_PLUGINS
        github_plugin = COMMAND_PLUGINS["github"]

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Get the repo information from GitHub:
        try:
            repo_result = github_plugin.check_gh_for_existing_repo(repo, org)

            if not repo_result:
                send_error(data["channel"],
                           "@{}: This repository does not exist in {}!".format(user_data["name"], org))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))
            return

        which = "pro" if repo_result["private"] else "public"

        try:
            # Sync with Travis CI so that it knows about the repo:
            send_info(data["channel"], ":skull: Need to sync Travis CI with GitHub. Please wait...")
            self.sync_with_travis(which)

            send_info(data["channel"], ":guitar: Synced! Going to enable Travis CI on the repo now...")

            travis_data = self.look_for_repo(which, repo_result)
            if not travis_data:
                send_error(data["channel"], "@{}: Couldn't find the repo in Travis for some reason...\n\n".format(
                    user_data["name"]))
                return

            # Is it already enabled?
            if travis_data["active"]:
                send_success(data["channel"],
                             "@{}: Travis CI is already enabled on {}/{}.\n\n".format(
                                 user_data["name"], org, repo))
                return

            # Enable it:
            self.enable_travis_on_repo(which, repo_result)

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem communicating with Travis CI:\n\n{}".format(user_data["name"], e))
            return

        message = "@{}: Travis CI has been enabled on {}/{}.\n\n".format(user_data["name"], org, repo)
        send_success(data["channel"], message)

    def sync_with_travis(self, which):
        """
        Syncs Travis CI with GitHub to ensure that it can see all the latest
        :param which:
        :return:
        """
        result = requests.post("{base}/user/{userid}/sync".format(base=TRAVIS_URLS[which],
                                                                  userid=self.credentials[which]["id"]),
                               headers=self._make_headers(which))
        if result.status_code != 200:
            raise TravisCIException("Travis CI Status Code: {}".format(result.status_code))

        time.sleep(2)  # Eventual consistency issues may exist?

        while True:
            response = requests.get("{base}/user/{userid}".format(base=TRAVIS_URLS[which],
                                                                  userid=self.credentials[which]["id"]),
                                    headers=self._make_headers(which))
            if response.status_code != 200:
                raise TravisCIException("Sync Status Code: {}".format(response.status_code))

            result = json.loads(response.text)

            if not result["is_syncing"]:
                break

            time.sleep(2)

    def look_for_repo(self, which, repo_dict):
        """
        This will check if a repository is currently seen in Travis CI.
        :param which:
        :param repo_dict:
        :return:
        """
        result = requests.get("{base}/repo/{id}".format(base=TRAVIS_URLS[which],
                                                        id=repo_dict["full_name"].replace("/", "%2F")),
                              headers=self._make_headers(which))

        if result.status_code == 404:
            return None

        elif result.status_code != 200:
            raise TravisCIException("Repo Lookup Status Code: {}".format(result.status_code))

        return json.loads(result.text)

    def enable_travis_on_repo(self, which, repo_dict):
        """
        This will enable Travis CI on a specified repository.
        :param which:
        :param repo_dict:
        :return:
        """
        result = requests.post("{base}/repo/{repo}/activate".format(base=TRAVIS_URLS[which],
                                                                    repo=repo_dict["full_name"].replace("/", "%2F")),
                               headers=self._make_headers(which))

        if result.status_code != 200:
            raise TravisCIException("Enable Repo Status Code: {}".format(result.status_code))

    def _make_headers(self, which):
        return {
            "User-Agent": USER_AGENT,
            "Authorization": "token {}".format(self.credentials[which]["token"]),
            "Travis-API-Version": "3"
        }
