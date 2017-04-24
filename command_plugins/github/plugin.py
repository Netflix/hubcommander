"""
.. module: hubcommander.github.plugin
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import argparse
import json

import requests
import time
import validators
from tabulate import tabulate

from hubcommander.bot_components.bot_classes import BotCommander
from hubcommander.bot_components.slack_comm import send_info, send_success, send_error, send_raw, preformat_args, preformat_args_with_spaces, \
    extract_repo_name, parse_toggles, TOGGLE_ON_VALUES, TOGGLE_OFF_VALUES
from hubcommander.command_plugins.github.config import (GITHUB_URL, GITHUB_VERSION, ORGS, USER_COMMAND_DICT)


class GitHubPlugin(BotCommander):
    def __init__(self):
        super().__init__()

        self.commands = {
            "!ListOrgs": {
                "command": "!ListOrgs",
                "func": self.list_org_command,
                "user_data_required": False,
                "help": "Lists the GitHub organizations that are managed.",
                "enabled": True
            },
            "!CreateRepo": {
                "command": "!CreateRepo",
                "func": self.create_repo_command,
                "user_data_required": True,
                "help": "Creates a new PRIVATE [default] repository in the specified GitHub organization.",
                "enabled": True
            },
            "!AddCollab": {
                "command": "!AddCollab",
                "func": self.add_outside_collab_command,
                "user_data_required": True,
                "help": "Adds an outside collaborator to a specific repository in a specific GitHub organization.",
                "permitted_permissions": ["push", "pull"],   # To grant admin, add this to the config for
                "enabled": True                              # this command in the config.py.
            },
            "!SetDescription": {
                "command": "!SetDescription",
                "func": self.set_description_command,
                "user_data_required": True,
                "help": "Adds/Modifies a GitHub repo's description.",
                "enabled": True
            },
            "!SetHomepage": {
                "command": "!SetHomepage",
                "func": self.set_repo_homepage_command,
                "user_data_required": True,
                "help": "Adds/Modifies a GitHub repo's homepage URL.",
                "enabled": True
            },
            "!SetDefaultBranch": {
                "command": "!SetDefaultBranch",
                "func": self.set_default_branch_command,
                "user_data_required": True,
                "help": "Sets the default branch for a repo.",
                "enabled": True     # It is HIGHLY recommended you have auth enabled for this!!
            },
            "!ListPRs": {
                "command": "!ListPRs",
                "func": self.list_pull_requests,
                "user_data_required": True,
                "help": "List the Pull Requests for a repo.",
                "permitted_states": ["open", "closed", "all"],
                "enabled": True
            },
            "!DeleteRepo": {
                "command": "!DeleteRepo",
                "func": self.delete_repo_command,
                "user_data_required": True,
                "help": "Delete a GitHub repository.",
                "enabled": True     # It is HIGHLY recommended you have auth enabled for this!!
            },
            "!AddUserToTeam": {
                "command": "!AddUserToTeam",
                "func": self.add_user_to_team_command,
                "user_data_required": True,
                "help": "Adds a GitHub user to a specific team inside the organization.",
                "permitted_roles": ["member", "maintainer"],
                "enabled": True
            },
            "!SetBranchProtection": {
                "command": "!SetBranchProtection",
                "func": self.set_branch_protection_command,
                "user_data_required": True,
                "help": "Toggles the branch protection for a repo.",
                "enabled": True  # It is HIGHLY recommended you have auth enabled for this!!
            },
        }
        self.token = None

        # For org alias lookup convenience:
        self.org_lookup = None

    def setup(self, secrets, **kwargs):
        self.token = secrets["GITHUB"]

        # Create the lookup table:
        self.org_lookup = {}
        for org in ORGS.items():
            # The lookup table is the lowercase real name of the org, plus the aliases, along with
            # a tuple containing the full real name of the org, with the org dict details:
            self.org_lookup[org[0].lower()] = (org[0], org[1])
            for alias in org[1]["aliases"]:
                self.org_lookup[alias] = (org[0], org[1])

        # Add user-configurable arguments to the command_plugins dictionary:
        for cmd, keys in USER_COMMAND_DICT.items():
            self.commands[cmd].update(keys)

    @staticmethod
    def list_org_command(data):
        """
        The "!ListOrgs" command_plugins. Lists all organizations that this bot manages.
        :param data:
        :return:
        """
        headers = ["Alias", "Organization"]
        rows = []
        for org in ORGS.items():
            rows.append([org[0].lower(), org[0]])
            for alias in org[1]["aliases"]:
                rows.append([alias, org[0]])

        send_info(data["channel"], "```{}```".format(tabulate(rows, headers=headers)), markdown=True)

    def set_description_command(self, data, user_data):
        """
        Changes a repository description.

        Command is as follows: !setdescription <organization> <repo> <description>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('description', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args_with_spaces(data["text"], 1))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])
            description = args["description"].replace("<", "").replace(">", "")

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!SetDescription` usage is:\n```!SetDescription <OrgThatHasRepo> "
                                       "<Repo> <\"The Description in quotes\">```\n"
                                       "No special characters or spaces in the variables. \n"
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!SetDescription"].get("auth"):
            if not self.commands["!SetDescription"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!SetDescription"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        if not (self.check_if_repo_exists(data, user_data, reponame, real_org)):
            return

        # Great, modify the description:
        if not (self.make_repo_edit(data, user_data, reponame, real_org, description=description)):
            return

        # Done:
        if description == "":
            send_success(data["channel"],
                         "@{}: The {}/{} repository's description field has been cleared."
                         .format(user_data["name"], real_org, reponame), markdown=True)
        else:
            send_success(data["channel"],
                         "@{}: The {}/{} repository's description has been modified to:\n"
                         "`{}`.".format(user_data["name"], real_org, reponame, description), markdown=True)

    def set_repo_homepage_command(self, data, user_data):
        """
        Changes a repository's homepage.

        Command is as follows: !sethomepage <organization> <repo> <homepage>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('homepage', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args_with_spaces(data["text"], 1))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])

            # Remove the "<>" from the homepage url (Thanks Slack!)
            homepage = args["homepage"].replace("<", "").replace(">", "")

            if homepage != "":
                if not validators.url(homepage):
                    raise ValueError()

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except ValueError as _:
            send_error(data["channel"], '@{}: Invalid homepage url was sent in. It must be a well formed URL.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!SetHomepage` usage is:\n```!SetHomepage <OrgThatHasRepo> "
                                       "<Repo> <\"http://theHomePageUrlInQuotes\" - OR - \"\" to remove>```\n"
                                       "No special characters or spaces in the variables. \n"
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!SetHomepage"].get("auth"):
            if not self.commands["!SetHomepage"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!SetHomepage"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        if not (self.check_if_repo_exists(data, user_data, reponame, real_org)):
            return

        # Great, modify the homepage:
        if not (self.make_repo_edit(data, user_data, reponame, real_org, homepage=homepage)):
            return

        # Done:
        if homepage == "":
            send_success(data["channel"],
                         "@{}: The {}/{} repository's homepage field has been cleared."
                         .format(user_data["name"], real_org, reponame, homepage), markdown=True)
        else:
            send_success(data["channel"],
                         "@{}: The {}/{} repository's homepage has been modified to:\n"
                         "`{}`.".format(user_data["name"], real_org, reponame, homepage), markdown=True)

    def add_outside_collab_command(self, data, user_data):
        """
        Adds an outside collaborator a repository with a specified permission.

        Command is as follows: !addcollab <organization> <repo> <permission>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('outside_collab_id', type=str)
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('permission', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            outside_collab_id = args["outside_collab_id"]

            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])
            repo_access = args["permission"]

            # Check that the permissions and the org are correct:
            if repo_access not in self.commands["!AddCollab"]["permitted_permissions"]:
                raise KeyError("Permissions")

        except KeyError as ke:
            if "Permissions" in str(ke):
                p_str = " or ".join(["`{perm}`".format(perm=perm)
                                     for perm in self.commands["!AddCollab"]["permitted_permissions"]])
                send_error(data["channel"], '@{}: Invalid permission sent in.  Permissions must be {perms}.'
                           .format(user_data["name"], perms=p_str), markdown=True)
            else:
                send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                           .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!AddCollab` usage is:\n```!AddCollab <OutsideCollaboratorGitHubId> "
                                       "<OrgAliasThatContainsTheRepo> <RepoToAddAccessTo> "
                                       "<PermissionEitherPushOrPull>```"
                                       "\nNo special characters or spaces in the variables. "
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!AddCollab"].get("auth"):
            if not self.commands["!AddCollab"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!AddCollab"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        if not (self.check_if_repo_exists(data, user_data, reponame, real_org)):
            return

        # Check that the GitHub ID is actually real:
        try:
            found_user = self.get_github_user(outside_collab_id)

            if not found_user:
                send_error(data["channel"], "@{}: The GitHub user: {} does not exist.".format(user_data["name"],
                                                                                              outside_collab_id))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: A problem was encountered communicating with GitHub to verify the user's GitHub "
                       "id. Here are the details:\n{}".format(user_data["name"], str(e)))
            return

        # So: GitHub ID is real - and the repo exists -- grant access:
        try:
            self.add_outside_collab_to_repo(outside_collab_id, reponame, real_org, repo_access)

        except ValueError as ve:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as an outside collaborator.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(ve)))
            return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as an outside collaborator.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)))
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The GitHub user: `{}` has been added as an outside collaborator with `{}` "
                     "permissions to {}/{}.".format(user_data["name"], outside_collab_id, repo_access,
                                                    real_org, reponame),
                     markdown=True)

    def add_user_to_team_command(self, data, user_data):
        """
        Adds a GitHub user to a team with a specified role.

        Command is as follows: !addusertoteam <user_id> <organization> <team> <role>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('user_id', type=str)
            parser.add_argument('org', type=str)
            parser.add_argument('team', type=str)
            parser.add_argument('role', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            user_id = args["user_id"]

            real_org = self.org_lookup[args["org"]][0]
            team_name = args["team"]
            team_access = args["role"]

            # Check that the permissions and the org are correct:
            if team_access not in self.commands["!AddUserToTeam"]["permitted_roles"]:
                raise KeyError("Roles")

        except KeyError as ke:
            if "Roles" in str(ke):
                p_str = " or ".join(["`{perm}`".format(perm=perm)
                                     for perm in self.commands["!AddUserToTeam"]["permitted_roles"]])
                send_error(data["channel"], '@{}: Invalid roles sent in.  Roles must be {perms}.'
                           .format(user_data["name"], perms=p_str), markdown=True)
            else:
                send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                           .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!AddUserToTeam` usage is:\n```!AddUserToTeam <GitHubUserID> "
                                       "<OrgAlias> <TeamToAddAccessTo> "
                                       "<RoleEitherMemberOrMantainer>```"
                                       "\nNo special characters or spaces in the variables. "
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!AddUserToTeam"].get("auth"):
            if not self.commands["!AddUserToTeam"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!AddUserToTeam"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check if team exists, if it does return the id
        team_id = self.find_team_id_by_name(real_org, team_name)

        if not (team_id):
            send_error(data["channel"], "The GitHub team does not exist.")
            return

        # Check that the GitHub ID is actually real:
        try:
            found_user = self.get_github_user(user_id)

            if not found_user:
                send_error(data["channel"], "@{}: The GitHub user: {} does not exist.".format(user_data["name"],
                                                                                              user_id))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: A problem was encountered communicating with GitHub to verify the user's GitHub "
                       "id. Here are the details:\n{}".format(user_data["name"], str(e)))
            return

        # So: GitHub ID is real - and the team exists -- grant access:
        try:
            self.invite_user_to_gh_org_team(user_id, team_id, team_access)

        except ValueError as ve:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as a team member.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(ve)))
            return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as a team member.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)))
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The GitHub user: `{}` has been added as a team member with `{}` "
                     "permissions to {}/{}.".format(user_data["name"], user_id, team_access,
                                                    real_org, team_name),
                     markdown=True)

    def create_repo_command(self, data, user_data):
        """
        Creates a new repository (default is private unless the org is public only).

        Command is as follows: !createrepo <newrepo> <organization>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('new_repo', type=str)
            parser.add_argument('org', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            repo_to_add = args["new_repo"]

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!CreateRepo` usage is:\n```!CreateRepo <NewRepoName> "
                                       "<GitHubOrgAliasToPutTheRepoInToHere>```\nNo special characters or spaces in the "
                                       "variables.  Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!CreateRepo"].get("auth"):
            if not self.commands["!CreateRepo"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!CreateRepo"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check if the repo already exists:
        try:
            result = self.check_gh_for_existing_repo(repo_to_add, real_org)

            if result:
                send_error(data["channel"],
                           "@{}: This repository already exists in {}!".format(user_data["name"], real_org))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))

            return

        # Great!! Create the repository:
        try:
            visibility = True if not ORGS[real_org]["public_only"] else False
            self.create_new_repo(repo_to_add, real_org, visibility)
        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))
            return

        # Need to wait a bit to ensure that the repo actually exists.
        time.sleep(2)

        # Grant the proper teams access to the repository:
        try:
            for perm_dict in ORGS[real_org]["new_repo_teams"]:
                self.set_repo_permissions(repo_to_add, real_org, perm_dict["id"], perm_dict["perm"])

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem setting repo permissions for team {team}: \n\n{exc}".format(
                           user_data["name"], team=perm_dict["name"], exc=e))
            return

        # All done!
        message = "@{}: The new repo: {} has been created in {}.\n".format(user_data["name"], repo_to_add, real_org)
        message += "You can access the repo at: https://github.com/{org}/{repo}\n".format(org=real_org,
                                                                                          repo=repo_to_add)

        visibility = "PRIVATE" if visibility else "PUBLIC"

        message += "The repository is {visibility}.\n" \
                   "You are free to set up the repo as you like.\n".format(visibility=visibility)

        send_success(data["channel"], message)

    def delete_repo_command(self, data, user_data):
        """
        Deletes a repository.

        Command is as follows: !deleterepo <repo> <organization>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('repo', type=str)
            parser.add_argument('org', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            repo_to_remove = args["repo"]

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!DeleteRepo` usage is:\n```!DeleteRepo <RepoName> "
                                       "<GitHubOrgAliasToPutTheRepoInToHere>```\nNo special characters or spaces in the "
                                       "variables.  Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!DeleteRepo"].get("auth"):
            if not self.commands["!DeleteRepo"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!DeleteRepo"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check if the repo already exists:
        try:
            result = self.check_gh_for_existing_repo(repo_to_remove, real_org)

            if not result:
                send_error(data["channel"],
                           "@{}: This repository does not exist in {}!".format(user_data["name"], real_org))
                return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))

            return

        # Great! Delete the repository:
        try:
            self.delete_repo(repo_to_remove, real_org)
        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))
            return

        # All done!
        message = "@{}: The repo: {} has been deleted from {}.\n".format(user_data["name"],
                                                                         repo_to_remove, real_org)

        send_success(data["channel"], message)

    def set_default_branch_command(self, data, user_data):
        """
        Sets the default branch of a repo.

        Command is as follows: !setdefaultbranch <organization> <repo> <branch>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('branch', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])
            branch = args["branch"]

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!SetDefaultBranch` usage is:\n```!SetDefaultBranch <OrgThatHasRepo> "
                                       "<Repo> <NameOfBranch>```\n"
                                       "No special characters or spaces in the variables. \n"
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!SetDefaultBranch"].get("auth"):
            if not self.commands["!SetDefaultBranch"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!SetDefaultBranch"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        repo_data = self.check_gh_for_existing_repo(reponame, real_org)
        if not (repo_data):
            send_error(data["channel"],
                       "@{}: This repository does not exist in {}.".format(user_data["name"], real_org))
            return False

        # Check if the branch exists on that repo....
        if not (self.check_for_repo_branch(reponame, real_org, branch)):
            send_error(data["channel"],
                       "@{}: This repository does not have the branch: `{}`.".format(user_data["name"], branch),
                       markdown=True)
            return False

        # Great, set the default branch:
        if not (self.make_repo_edit(data, user_data, reponame, real_org, default_branch=branch)):
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The {}/{} repository's default branch has been set to: `{}`."
                     .format(user_data["name"], real_org, reponame, branch), markdown=True)

    def set_branch_protection_command(self, data, user_data):
        """
        Sets branch protection on a repo (CURRENTLY VERY LIMITED).

        Command is as follows: !setbranchprotection <organization> <repo> <branch> <on/off>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('branch', type=str)
            parser.add_argument('toggle', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])
            branch = args["branch"]
            toggle = parse_toggles(args["toggle"])

        except KeyError as _:
            send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                       .format(user_data["name"]), markdown=True)
            return

        except ValueError as _:
            valid_toggles = TOGGLE_ON_VALUES + TOGGLE_OFF_VALUES

            send_error(data["channel"], '@{}: Invalid toggle sent in. Must be one of: {}.'
                       .format(user_data["name"], ", ".join(valid_toggles)), markdown=True)
            return

        except SystemExit as _:
            send_info(data["channel"], "@{}: `!SetBranchProtection` usage is:\n```!SetBranchProtection "
                                       "<OrgThatHasRepo> <Repo> <NameOfBranch> <On|Off>```\n"
                                       "No special characters or spaces in the variables. \n"
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                                       "This will first check for the presence of the repo in the org before "
                                       "creating it."
                      .format(user_data["name"]), markdown=True)
            return

        # Auth?
        if self.commands["!SetBranchProtection"].get("auth"):
            if not self.commands["!SetBranchProtection"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!SetBranchProtection"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        repo_data = self.check_gh_for_existing_repo(reponame, real_org)
        if not (repo_data):
            send_error(data["channel"],
                       "@{}: This repository does not exist in {}.".format(user_data["name"], real_org))
            return False

        # Check if the branch exists on that repo....
        if not (self.check_for_repo_branch(reponame, real_org, branch)):
            send_error(data["channel"],
                       "@{}: This repository does not have the branch: `{}`.".format(user_data["name"], branch),
                       markdown=True)
            return False

        # Great, change the protection status:
        try:
            self.set_branch_protection(reponame, real_org, branch, toggle)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered setting branch protection.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)))
            return

        # Done:
        status = "ENABLED" if toggle else "DISABLED"
        send_success(data["channel"],
                     "@{}: The {}/{} repository's {} branch protection status is now: {}."
                     .format(user_data["name"], real_org, reponame, branch, status), markdown=True)

    def check_if_repo_exists(self, data, user_data, reponame, real_org):
        try:
            result = self.check_gh_for_existing_repo(reponame, real_org)

            if not result:
                send_error(data["channel"],
                           "@{}: This repository does not exist in {}.".format(user_data["name"], real_org))
                return False

            return True

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e))
            return False

    def make_repo_edit(self, data, user_data, reponame, real_org, **kwargs):
        try:
            self.modify_repo(reponame, real_org, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered modifying the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)))
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered setting the {} field.\n"
                       "Here are the details: {}".format(kwargs.keys()[0], user_data["name"], str(e)))
            return False

        return True

    def check_gh_for_existing_repo(self, repo_to_check, org):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'repos/{}/{}'.format(org, repo_to_check)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 200:
            return json.loads(response.text)

        if response.status_code != 404:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

        return None

    def get_repo_prs(self, data, user_data, reponame, real_org, state, **kwargs):
        try:

            return self.get_repo_pull_requests_http(reponame, real_org, state, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while getting pull requests from the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)))
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)))
            return False

    def get_github_user(self, github_id):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'users/{}'.format(github_id)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            message = 'Did not receive a proper status code from GitHub while checking if the user exists.\n' \
                      'The status code received was: {}'.format(response.status_code)
            raise requests.exceptions.RequestException(message)

        # return the user info:
        response_obj = json.loads(response.text)
        return response_obj

    def modify_repo(self, repo, org, **kwargs):
        """
        Reaches out to GH to modify repos.

        :param repo:
        :param org:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'repos/{}/{}'.format(org, repo)

        kwargs["name"] = repo

        response = requests.patch(
            '{}{}'.format(GITHUB_URL, api_part),
            data=json.dumps(kwargs),
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def get_repo_pull_requests_http(self, repo, org, state, **kwargs):
        """
        List pull requests associated with a repo.

        :param repo:
        :param org:
        :param state:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        api_part = 'repos/{}/{}/pulls?state={}'.format(org, repo, state)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def add_outside_collab_to_repo(self, outside_collab_id, repo_name, real_org, permission):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        data = {"permission": permission}

        # Add the outside collab to the repo:
        api_part = 'repos/{}/{}/collaborators/{}'.format(real_org, repo_name, outside_collab_id)
        response = requests.put('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data), headers=headers, timeout=10)

        if response.status_code != 204:
            raise ValueError(response.status_code)

    def create_new_repo(self, repo_to_create, org, visibility):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'orgs/{}/repos'.format(org)

        data = {
            "name": repo_to_create,
            "private": visibility,  # Depends on the org.
            "has_wiki": True
        }

        response = requests.post(
            '{}{}'.format(GITHUB_URL, api_part),
            data=json.dumps(data),
            headers=headers,
            timeout=10
        )

        if response.status_code != 201:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def delete_repo(self, repo_to_delete, org):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'repos/{org}/{repo}'.format(org=org, repo=repo_to_delete)

        response = requests.delete(
            '{}{}'.format(GITHUB_URL, api_part),
            headers=headers,
            timeout=10
        )

        if response.status_code != 204:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def set_repo_permissions(self, repo_to_set, org, team, permission):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'teams/{}/repos/{}/{}'.format(team, org, repo_to_set)

        data = {
            "permission": permission
        }

        response = requests.put(
            '{}{}'.format(GITHUB_URL, api_part),
            data=json.dumps(data),
            headers=headers,
            timeout=10
        )

        if response.status_code != 204:
            message = 'An error was encountered communicating with GitHub (setting repo perms): Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def check_for_repo_branch(self, repo, org, branch):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'repos/{}/{}/branches/{}'.format(org, repo, branch)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 200:
            return True

        if response.status_code != 404:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

        return False

    def set_branch_protection(self, repo, org, branch, enabled):
        # TODO: Need to figure out how to do more complex things with this.
        #       Currently, this just does very simple enabling and disabling of branch protection
        # See: https://developer.github.com/v3/repos/branches/#enabling-and-disabling-branch-protection
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': "application/vnd.github.loki-preview+json"
        }
        api_part = 'repos/{}/{}/branches/{}'.format(org, repo, branch)

        data = {
            "protection": {
                "enabled": enabled
            }
        }

        response = requests.patch('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data), headers=headers, timeout=10)

        if response.status_code != 200:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def check_if_user_is_member_of_org(self, github_id, org):
        # Check if the user exists first:
        user = self.get_github_user(github_id)

        if not user:
            return None

        # Check if that user is a member of the org in question:
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }
        api_part = 'orgs/{}/members/{}'.format(org, user["login"])
        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        # Per GitHub API, if 204, then already a member; if 404, then not a member:
        if response.status_code == 204:
            return True

        elif response.status_code != 404:
            raise ValueError("GitHub Problem: Checking membership, status code: {}".format(response.status_code))

        return False

    def invite_user_to_gh_org_team(self, github_id, team_id, role):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        data = {"role": role}

        # Add the GitHub user to the team:
        api_part = 'teams/{}/memberships/{}'.format(team_id, github_id)
        response = requests.put('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data), headers=headers, timeout=10)

        if response.status_code != 200:
            raise ValueError("GitHub Problem: Adding to team, status code: {}".format(response.status_code))

    def find_team_id_by_name(self, org, team_name):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        # Get all teams inside the organzation:
        api_part = 'orgs/{}/teams'.format(org)
        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code != 200:
            raise ValueError("GitHub Problem: Could not list teams -- received error code: {}".format(response.status_code))

        # Check if the provided team_name belongs to a team inside the organization:
        for x in response.json():
            if x["slug"] == team_name:
                return x["id"]

        return False

    def list_pull_requests(self, data, user_data):
        """
        List the Pull Requests for a repo.

        Command is as follows: !listprs <organization> <repo> <state>
        :param data:
        :return:
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('org', type=str)
            parser.add_argument('repo', type=str)
            parser.add_argument('state', type=str)

            args, unknown = parser.parse_known_args(args=preformat_args(data["text"]))
            if len(unknown) > 0:
                raise SystemExit()

            args = vars(args)

            # Check that we can use this org:
            real_org = self.org_lookup[args["org"]][0]
            reponame = extract_repo_name(args["repo"])

            # Check if the sent state is permitted
            state = args["state"]
            if state not in self.commands["!ListPRs"]["permitted_states"]:
                raise KeyError("PRStates")

        except KeyError as ke:
            if "PRStates" in str(ke):
                s_str = " or ".join(["`{perm_state}`".format(perm_state=perm_state)
                                     for perm_state in self.commands["!ListPRs"]["permitted_states"]])
                send_error(data["channel"], '@{}: Invalid state sent in.  States must be {perm_states}.'
                           .format(user_data["name"], perm_states=s_str), markdown=True)
            else:
                send_error(data["channel"], '@{}: Invalid orgname sent in.  Run `!ListOrgs` to see the valid orgs.'
                           .format(user_data["name"]), markdown=True)
            return

        except SystemExit as _:
            s_str = " or ".join(["`{perm_state}`".format(perm_state=perm_state)
                                 for perm_state in self.commands["!ListPRs"]["permitted_states"]])
            send_info(data["channel"], "@{}: `!ListPRs` usage is:\n```!ListPRs <OrgThatHasRepo> "
                                       "<Repo> <State>```\n"
                                       "`<State>` must one of: {perm_states}\n"
                                       "No special characters or spaces in the variables. \n"
                                       "Run `!ListOrgs` to see the list of GitHub Organizations that I manage. "
                      .format(user_data["name"], perm_states=s_str), markdown=True)
            return

        # Auth?
        if self.commands["!ListPRs"].get("auth"):
            if not self.commands["!ListPRs"]["auth"]["plugin"].authenticate(
                    data, user_data, **self.commands["!ListPRs"]["auth"]["kwargs"]):
                return

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]))

        # Check that the repo exists:
        repo_data = self.check_gh_for_existing_repo(reponame, real_org)
        if not (repo_data):
            send_error(data["channel"],
                       "@{}: This repository does not exist in {}.".format(user_data["name"], real_org))
            return

        # Grab all PRs [All states]
        pull_requests = self.get_repo_prs(data, user_data, reponame, real_org, state)
        if not (pull_requests):
            if isinstance(pull_requests, list):
                send_info(data["channel"],
                          "@{}: No matching pull requests were found in *{}*.".format(user_data["name"], reponame))
            return

        headers = ["#PR", "Title", "Opened by", "Assignee", "State"]

        rows = []
        for pr in pull_requests:
            assignee = pr['assignee']['login'] if pr['assignee'] is not None else '-'
            rows.append([pr['number'],pr['title'], pr['user']['login'], assignee,pr['state'].title()])
        # Done:
        send_raw(data["channel"], text="Repository: *{}* \n\n```{}```".format(reponame, tabulate(rows, headers=headers,
                                                                                                 tablefmt='orgtbl')))
