"""
.. module: hubcommander.travis_ci.plugin
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import argparse
import json
import time

import requests

from bot_components.bot_classes import BotCommander
from bot_components.slack_comm import extract_repo_name, send_error, send_info, preformat_args, send_success
from command_plugins.travis_ci.config import USER_COMMAND_DICT, USER_AGENT

TRAVIS_URLS = {
    "pro": "https://api.travis-ci.com",
    "public": "https://api.travis-ci.org"
}


class TravisCIException(Exception):
    pass


class TravisPlugin(BotCommander):
    def __init__(self):
        super().__init__()

        self.commands = {
            "!EnableTravis": {
                "command": "!EnableTravis",
                "func": self.enable_travis_command,
                "help": "Enables Travis CI on a GitHub Repo.",
                "user_data_required": True,
                "enabled": True
            }
        }

        self.credentials = None

    def setup(self, secrets, **kwargs):
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

    def enable_travis_command(self, data, user_data):
        """
        Enables Travis CI on a repository within the organization.

        Command is as follows: !enabletravis <organization> <repo>
        :param data:
        :return:
        """
        from command_plugins.enabled_plugins import GITHUB_PLUGIN
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            repo_to_set = extract_repo_name(args["repo"])

            # Check that we can use this org:
            real_org = GITHUB_PLUGIN.org_lookup[args["org"]][0]

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!EnableTravis` usage is:\n```!EnableTravis <Organization> <Repo>"
                                       "```\nNo special characters or spaces in the variables. "
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!EnableTravis"].get("auth"):
            if not self.commands["!EnableTravis"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!EnableTravis"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Get the repo information from GitHub:
        try:
            repo_result = GITHUB_PLUGIN.check_gh_for_existing_repo(repo_to_set, real_org)

            if not repo_result:
                send_error(data["channel"],
                           "@{}: This repository does not exist in {}!".format(user_data["name"], real_org))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))
            return

        which = "pro" if repo_result["private"] else "public"

        try:
            # Check that the repo even exists:
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
                                 user_data["name"], real_org, repo_to_set))
                return

            # Enable it:
            self.enable_travis_on_repo(which, repo_result)

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem communicating with Travis CI:\n\n{}".format(user_data["name"], e))
            return

        message = "@{}: Travis CI has been enabled on {}/{}.\n\n".format(user_data["name"], real_org, repo_to_set)
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
