"""
.. module: hubcommander.command_plugins.github.plugin
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json

import requests
import time
from tabulate import tabulate

from hubcommander.bot_components.bot_classes import BotCommander
from hubcommander.bot_components.decorators import hubcommander_command, auth
from hubcommander.bot_components.slack_comm import send_info, send_success, send_error, send_raw
from hubcommander.bot_components.parse_functions import extract_repo_name, parse_toggles
from hubcommander.command_plugins.github.config import GITHUB_URL, GITHUB_VERSION, ORGS, USER_COMMAND_DICT
from hubcommander.command_plugins.github.parse_functions import lookup_real_org, validate_homepage
from hubcommander.command_plugins.github.decorators import repo_must_exist, github_user_exists, branch_must_exist


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
                "permitted_permissions": ["push", "pull"],  # To grant admin, add this to the config for
                "enabled": True  # this command in the config.py.
            },
            "!SetRepoPermissions": {
                "command": "!SetRepoPermissions",
                "func": self.add_team_To_repo,
                "user_data_required": True,
                "help": "Adds a team to a specific repository in a specific GitHub organization.",
                "permitted_permissions": ["push", "pull"],  # To grant admin, add this to the config for
                "enabled": True  # this command in the config.py.
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
                "enabled": True  # It is HIGHLY recommended you have auth enabled for this!!
            },
            "!ListPRs": {
                "command": "!ListPRs",
                "func": self.list_pull_requests_command,
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
                "enabled": True  # It is HIGHLY recommended you have auth enabled for this!!
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
            "!ListKeys": {
                "command": "!ListKeys",
                "func": self.list_deploy_keys_command,
                "user_data_required": True,
                "help": "List the Deploy Keys for a repo.",
                "enabled": True
            },
            "!AddKey": {
                "command": "!AddKey",
                "func": self.add_deploy_key_command,
                "user_data_required": True,
                "help": "Add Deploy Key for a repo.",
                "enabled": True
            },
            "!DeleteKey": {
                "command": "!DeleteKey",
                "func": self.delete_deploy_key_command,
                "user_data_required": True,
                "help": "Delete Deploy Key from a repo.",
                "enabled": True
            },
            "!GetKey": {
                "command": "!GetKey",
                "func": self.get_deploy_key_command,
                "user_data_required": True,
                "help": "Get Deploy Key Public Key",
                "enabled": True
            },
            "!SetTopics": {
                "command": "!SetTopics",
                "func": self.set_repo_topics_command,
                "user_data_required": True,
                "help": "Sets the Topics for a GitHub repo",
                "enabled": True
            }
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
        The "!ListOrgs" command. Lists all organizations that this bot manages.
        :param data:
        :return:
        """
        headers = ["Alias", "Organization"]
        rows = []
        for org in ORGS.items():
            rows.append([org[0].lower(), org[0]])
            for alias in org[1]["aliases"]:
                rows.append([alias, org[0]])

        send_info(data["channel"], "```{}```".format(tabulate(rows, headers=headers)), markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!SetDescription",
        usage="!SetDescription <OrgWithRepo> <Repo> <\"The description in quotes\">",
        description="This will set the repository's description.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The repository to set the description on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="description", properties=dict(type=str, help="The description to set in quotes. (Empty quotes "
                                                                    "clears)"),
                 lowercase=False),
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def set_description_command(self, data, user_data, org, repo, description):
        """
        Changes a repository description.

        Command is as follows: !setdescription <organization> <repo> <description>
        :param data:
        :param user_data:
        :param org:
        :param repo:
        :param description:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Modify the description:
        if not (self.make_repo_edit(data, user_data, repo, org, description=description)):
            return

        if description == "":
            send_success(data["channel"],
                         "@{}: The {}/{} repository's description field has been cleared."
                         .format(user_data["name"], org, repo), markdown=True, thread=data["ts"])
        else:
            send_success(data["channel"],
                         "@{}: The {}/{} repository's description has been modified to:\n"
                         "`{}`.".format(user_data["name"], org, repo, description), markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!SetHomepage",
        usage="!SetHomepage <OrgWithRepo> <Repo> <\"http://theHomePageUrlInQuotes\" - OR - \"\" to remove>",
        description="This will set the repository's homepage.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The repository to set the homepage on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="homepage", properties=dict(type=str, help="The homepage to set in quotes. (Empty quotes "
                                                                 "clears)"),
                 validation_func=validate_homepage, validation_func_kwargs={})
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def set_repo_homepage_command(self, data, user_data, org, repo, homepage):
        """
        Changes a repository's homepage.

        Command is as follows: !sethomepage <organization> <repo> <homepage>
        :param data:
        :param user_data:
        :param org:
        :param repo:
        :param homepage:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Modify the homepage:
        if not (self.make_repo_edit(data, user_data, repo, org, homepage=homepage)):
            return

        # Done:
        if homepage == "":
            send_success(data["channel"],
                         "@{}: The {}/{} repository's homepage field has been cleared."
                         .format(user_data["name"], org, repo, homepage), markdown=True, thread=data["ts"])
        else:
            send_success(data["channel"],
                         "@{}: The {}/{} repository's homepage has been modified to:\n"
                         "`{}`.".format(user_data["name"], org, repo, homepage), markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!AddCollab",
        usage="!AddCollab <OutsideCollabId> <OrgWithRepo> <Repo> <Permission>",
        description="This will add an outside collaborator to a repository with the given permission.",
        required=[
            dict(name="collab", properties=dict(type=str, help="The outside collaborator's GitHub ID.")),
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The repository to add the outside collaborator to."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="permission", properties=dict(type=str.lower, help="The permission to grant, must be one "
                                                                         "of: `{values}`"),
                 choices="permitted_permissions"),
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    @github_user_exists("collab")
    def add_outside_collab_command(self, data, user_data, collab, org, repo, permission):
        """
        Adds an outside collaborator a repository with a specified permission.

        Command is as follows: !addcollab <outside_collab_id> <organization> <repo> <permission>
        :param permission:
        :param repo:
        :param org:
        :param collab:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grant access:
        try:
            self.add_outside_collab_to_repo(collab, repo, org, permission)

        except ValueError as ve:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as an outside collaborator.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(ve)), thread=data["ts"])
            return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as an outside collaborator.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The GitHub user: `{}` has been added as an outside collaborator with `{}` "
                     "permissions to {}/{}.".format(user_data["name"], collab, permission,
                                                    org, repo),
                     markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!SetRepoPermissions",
        usage="!SetRepoPermissions <Team> <OrgWithRepo> <Repo> <Permission>",
        description="This will add an outside collaborator to a repository with the given permission.",
        required=[
            dict(name="team", properties=dict(type=str, help="The team's GitHub ID.")),
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The repository to add the outside collaborator to."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="permission", properties=dict(type=str.lower, help="The permission to grant, must be one "
                                                                         "of: `{values}`"),
                 choices="permitted_permissions")
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def add_team_to_repo(self, data, user_data, team, org, repo, permission):
        """
        Adds a team to a repository with a specified permission.

        Command is as follows: !SetRepoPermissions <Team> <OrgWithRepo> <Repo> <Permission>
        :param permission:
        :param repo:
        :param org:
        :param teamid:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grant access:
        try:
            self.set_repo_permissions(repo, org, team, permission)

        except ValueError as ve:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the team.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(ve)), thread=data["ts"])
            return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the team.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The GitHub team: `{}` has been added to the repo with `{}` "
                     "permissions to {}/{}.".format(user_data["name"], team, permission,
                                                    org, repo),
                     markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!AddUserToTeam",
        usage="!AddUserToTeam <UserGitHubId> <Org> <Team> <Role>",
        description="This will add a GitHub user to a team with a specified role.",
        required=[
            dict(name="user_id", properties=dict(type=str, help="The user's GitHub ID.")),
            dict(name="org", properties=dict(type=str, help="The organization that contains the team."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="team", properties=dict(type=str, help="The team to add the user to.")),
            dict(name="role", properties=dict(type=str.lower, help="The role to grant the user. "
                                                                   "Must be one of: `{values}`"),
                 choices="permitted_roles"),
        ],
        optional=[]
    )
    @auth()
    @github_user_exists("user_id")
    def add_user_to_team_command(self, data, user_data, user_id, org, team, role):
        """
        Adds a GitHub user to a team with a specified role.

        Command is as follows: !addusertoteam <user_id> <organization> <team> <role>
        :param role:
        :param team:
        :param org:
        :param user_id:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Check if team exists, if it does return the id
        team_id = self.find_team_id_by_name(org, team)

        if not team_id:
            send_error(data["channel"], "The GitHub team does not exist.", thread=data["ts"])
            return

        # Do it:
        try:
            self.invite_user_to_gh_org_team(user_id, team_id, role)

        except ValueError as ve:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as a team member.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(ve)), thread=data["ts"])
            return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered adding the user as a team member.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The GitHub user: `{}` has been added as a team member with `{}` "
                     "permissions to {}/{}.".format(user_data["name"], user_id, role,
                                                    org, team),
                     markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!CreateRepo",
        usage="!CreateRepo <OrgToCreateRepoIn> <NewRepoName>",
        description="This will create a new repository on GitHub.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization to create the repo in."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the new repo to create."),
                 lowercase=False, validation_func=extract_repo_name, validation_func_kwargs={}),
        ],
        optional=[
            # TODO: Need to add support for optional teams to add. See https://github.com/Netflix/hubcommander/issues/28
        ]
    )
    @auth()
    def create_repo_command(self, data, user_data, org, repo):
        """
        Creates a new repository (default is private unless the org is public only).

        Command is as follows: !createrepo <organization> <new_repo>
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Check if the repo already exists:
        try:
            result = self.check_gh_for_existing_repo(repo, org)

            if result:
                # Check if the repo was renamed:
                if "{}/{}".format(org, repo) == result["full_name"]:
                    send_error(data["channel"],
                               "@{}: This repository already exists in {}!".format(user_data["name"], org),
                               thread=data["ts"])
                    return

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e), thread=data["ts"])

            return

        # Great!! Create the repository:
        try:
            visibility = True if not ORGS[org]["public_only"] else False
            self.create_new_repo(repo, org, visibility)
        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e), thread=data["ts"])
            return

        # Need to wait a bit to ensure that the repo actually exists.
        time.sleep(2)

        # Grant the proper teams access to the repository:
        try:
            for perm_dict in ORGS[org]["new_repo_teams"]:
                self.set_repo_permissions(repo, org, perm_dict["id"], perm_dict["perm"])

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem setting repo permissions for team {team}: \n\n{exc}".format(
                           user_data["name"], team=perm_dict["name"], exc=e), thread=data["ts"])
            return

        # All done!
        message = "@{}: The new repo: {} has been created in {}.\n".format(user_data["name"], repo, org)
        message += "You can access the repo at: https://github.com/{org}/{repo}\n".format(org=org,
                                                                                          repo=repo)

        visibility = "PRIVATE" if visibility else "PUBLIC"

        message += "The repository is {visibility}.\n" \
                   "You are free to set up the repo as you like.\n".format(visibility=visibility)

        send_success(data["channel"], message, thread=data["ts"])

    @hubcommander_command(
        name="!DeleteRepo",
        usage="!DeleteRepo <OrgThatHasRepo> <RepoToDelete>",
        description="This will delete a repo from a GitHub organization.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the new repo to delete."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def delete_repo_command(self, data, user_data, org, repo):
        """
        Deletes a repository.

        Command is as follows: !deleterepo <organization> <repo>
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Delete the repository:
        try:
            self.delete_repo(repo, org)
        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e), thread=data["ts"])
            return

        # All done!
        message = "@{}: The repo: {} has been deleted from {}.\n".format(user_data["name"], repo, org)
        send_success(data["channel"], message, thread=data["ts"])

    @hubcommander_command(
        name="!SetDefaultBranch",
        usage="!SetDefaultBranch <OrgThatHasRepo> <Repo> <BranchName>",
        description="This will set the default branch on a GitHub repo.\n\n"
                    "Please Note: GitHub prefers lowercase branch names. You may encounter issues "
                    "with uppercase letters.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to set the default on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="branch", properties=dict(type=str, help="The name of the branch to set as default. "
                                                               "(Case-Sensitive)"), lowercase=False),
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    @branch_must_exist()
    def set_default_branch_command(self, data, user_data, org, repo, branch):
        """
        Sets the default branch of a repo.

        Command is as follows: !setdefaultbranch <organization> <repo> <branch>
        :param branch:
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Set the default branch:
        if not (self.make_repo_edit(data, user_data, repo, org, default_branch=branch)):
            return

        # Done:
        send_success(data["channel"],
                     "@{}: The {}/{} repository's default branch has been set to: `{}`."
                     .format(user_data["name"], org, repo, branch), markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!SetBranchProtection",
        usage="!SetBranchProtection <OrgThatHasRepo> <Repo> <BranchName> <On|Off>",
        description="This will enable basic branch protection to a GitHub repo.\n\n"
                    "Please Note: GitHub prefers lowercase branch names. You may encounter issues "
                    "with uppercase letters.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to set the default on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="branch", properties=dict(type=str, help="The name of the branch to set as default. "
                                                               "(Case-Sensitive)"), lowercase=False),
            dict(name="toggle", properties=dict(type=str, help="Toggle to enable or disable branch protection"),
                 validation_func=parse_toggles, validation_func_kwargs={})
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    @branch_must_exist()
    def set_branch_protection_command(self, data, user_data, org, repo, branch, toggle):
        """
        Sets branch protection on a repo (CURRENTLY VERY LIMITED).

        Command is as follows: !setbranchprotection <organization> <repo> <branch> <on/off>
        :param toggle:
        :param branch:
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Change the protection status:
        try:
            self.set_branch_protection(repo, org, branch, toggle)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered setting branch protection.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return

        # Done:
        status = "ENABLED" if toggle else "DISABLED"
        send_success(data["channel"],
                     "@{}: The {}/{} repository's {} branch protection status is now: {}."
                     .format(user_data["name"], org, repo, branch, status), markdown=True, thread=data["ts"])

    @hubcommander_command(
        name="!ListPRs",
        usage="!ListPRs <OrgThatHasRepo> <Repo> <State>",
        description="This will list pull requests for a repo.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to list PRs on."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="state", properties=dict(type=str.lower, help="The state of the PR. Must be one of: `{values}`"),
                 choices="permitted_states")
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def list_pull_requests_command(self, data, user_data, org, repo, state):
        """
        List the Pull Requests for a repo.

        Command is as follows: !listprs <organization> <repo> <state>
        :param state:
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grab all PRs [All states]
        pull_requests = self.get_repo_prs(data, user_data, repo, org, state)
        if not pull_requests:
            if isinstance(pull_requests, list):
                send_info(data["channel"],
                          "@{}: No matching pull requests were found in *{}*.".format(user_data["name"], repo),
                          thread=data["ts"])
            return

        headers = ["#PR", "Title", "Opened by", "Assignee", "State"]

        rows = []
        for pr in pull_requests:
            assignee = pr['assignee']['login'] if pr['assignee'] is not None else '-'
            rows.append([pr['number'], pr['title'], pr['user']['login'], assignee, pr['state'].title()])

        # Done:
        send_raw(data["channel"], text="Repository: *{}* \n\n```{}```".format(repo, tabulate(rows, headers=headers,
                                                                                             tablefmt='orgtbl')),
                 thread=data["ts"])

    @hubcommander_command(
        name="!ListKeys",
        usage="!ListKeys <OrgThatHasRepo> <Repo>",
        description="This will list deploy keys for a repo.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to list deploy keys on."),
                 validation_func=extract_repo_name, validation_func_kwargs={})
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def list_deploy_keys_command(self, data, user_data, org, repo):
        """
        List the Deploy Keys for a repo.

        Command is as follows: !ListKeys <organization> <repo>
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grab all Deploy Keys
        deploy_keys = self.get_repo_deploy_keys(data, user_data, repo, org)

        if not (deploy_keys):
            if isinstance(deploy_keys, list):
                send_info(data["channel"],
                          "@{}: No deploy keys were found in *{}*.".format(user_data["name"], repo), thread=data["ts"])
            return

        headers = ["ID#", "Title", "Read-only", "Created"]

        rows = []
        for key in deploy_keys:
            # Set a default readonly state
            readonly = 'True'
            if not key['read_only']:
                readonly = 'False'

            rows.append([key['id'], key['title'], readonly, key['created_at']])

        # Done:
        send_raw(data["channel"], text="Deploy Keys: *{}* \n\n```{}```".format(repo, tabulate(rows, headers=headers,
                                                                                              tablefmt='orgtbl')),
                 thread=data["ts"])

    @hubcommander_command(
        name="!AddKey",
        usage="!AddKey <OrgThatHasRepo> <Repo> <KeyTitle> <ReadOnlyToggle on|off> <\"KeyInQuotes\">",
        description="This will add a deploy key to a repo.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to add a deploy key to."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="title", properties=dict(type=str, help="The name of the deploy key. (Case-Sensitive)"),
                 lowercase=False),
            dict(name="readonly", properties=dict(type=str, help="Toggle to indicate if this key is read-only."),
                 validation_func=parse_toggles, validation_func_kwargs={}),
            dict(name="pubkey", properties=dict(type=str, help="The SSH *PUBLIC* key in quotes. (Case-Sensitive)"),
                 lowercase=False)
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def add_deploy_key_command(self, data, user_data, org, repo, title, readonly, pubkey):
        """
        Add a Deploy Key to a repo.

        Command is as follows: !AddKey <organization> <repo> <title> <readonly> "<pubkey>"
        :param pubkey:
        :param title:
        :param repo:
        :param org:
        :param user_data:
        :param readonly:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Add the Deploy Key
        result = self.add_repo_deploy_key(data, user_data, repo, org, title, pubkey, readonly)

        # If we have an error due to invalid key, we are returning False from the API response method
        if not result:
            send_error(data["channel"], "@{}: The deploy key entered was invalid -- or -- it already exists."
                       .format(user_data["name"], repo), thread=data["ts"])
            return

        if not result.get('id'):
            send_error(data["channel"], "@{}: Adding deploy key failed.".format(user_data["name"], repo),
                       thread=data["ts"])
            return

        # Done:
        send_raw(data["channel"],
                 text="Deploy Key *{}* with ID *{}* successfully added to *{}*\n\n".format(result['title'],
                                                                                           result['id'], repo),
                 thread=data["ts"])

    @hubcommander_command(
        name="!DeleteKey",
        usage="!DeleteKey <OrgThatHasRepo> <Repo> <KeyId>",
        description="This will delete the specified deploy key from a repo.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to remove the deploy key from."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="id", properties=dict(type=int, help="The ID of the key. Please run !ListKeys to get this."))
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def delete_deploy_key_command(self, data, user_data, org, repo, id):
        """
        Delete a Deploy Key from a repo.

        Command is as follows: !DeleteKey <organization> <repo> <id>
        :param id:
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grab the Deploy Key (check that it exists)
        deploy_key = self.get_repo_deploy_key_by_id(data, user_data, repo, org, id)
        if not deploy_key:
            if deploy_key is None:
                send_error(data["channel"],
                           "@{}: Deploy Key with ID: `{}` is not present for the {}/{} repo.".format(user_data["name"],
                                                                                                     id, org, repo),
                           markdown=True, thread=data["ts"])
            else:
                send_error(data["channel"], "@{}: Error Retrieving Deploy Key `{}`.".format(user_data["name"], id),
                           markdown=True, thread=data["ts"])

            return

        # Delete the Deploy Key
        result = self.delete_repo_deploy_key(data, user_data, repo, org, id)

        if not result:
            send_info(data["channel"], "@{}: Error deleting deploy key ID *{}*.".format(user_data["name"], id),
                      markdown=True, thread=data["ts"])
            return

        # Done:
        send_raw(data["channel"], text="Deploy Key ID *{}* successfully deleted from *{}*\n\n".format(id, repo),
                 thread=data["ts"])

    @hubcommander_command(
        name="!GetKey",
        usage="!GetKey <OrgThatHasRepo> <Repo> <KeyId>",
        description="This will fetch the details of a specified deploy key from a repo.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to fetch the deploy key "
                                                             "details from."),
                 validation_func=extract_repo_name, validation_func_kwargs={}),
            dict(name="id", properties=dict(type=int, help="The ID of the key. Please run !ListKeys to get this."))
        ],
        optional=[]
    )
    @auth()
    @repo_must_exist()
    def get_deploy_key_command(self, data, user_data, org, repo, id):
        """
        Get a given Deploy Key.

        Command is as follows: !GetKey <organization> <repo> <id>
        :param id:
        :param repo:
        :param org:
        :param user_data:
        :param data:
        :return:
        """
        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Grab the Deploy Key
        deploy_key = self.get_repo_deploy_key_by_id(data, user_data, repo, org, id)

        if not deploy_key:
            if deploy_key is None:
                send_error(data["channel"],
                           "@{}: Deploy Key with ID: `{}` is not present for the {}/{} repo.".format(user_data["name"],
                                                                                                     id, org, repo),
                           markdown=True, thread=data["ts"])
            else:
                send_error(data["channel"], "@{}: Error Retrieving Deploy Key `{}`.".format(user_data["name"], id),
                           markdown=True, thread=data["ts"])

            return

        # Done:
        send_info(data["channel"],
                  "@{}: Deploy Key ID `{}`: ```{}```".format(user_data["name"], id, deploy_key['key']), markdown=True,
                  thread=data["ts"])

    @hubcommander_command(
        name="!SetTopics",
        usage="!SetTopics <OrgThatContainsRepo> <RepoToSetTopicsOn> <CommaSeparatedListOfTopics>",
        description="This sets (or clears) the topics for a repository on GitHub.",
        required=[
            dict(name="org", properties=dict(type=str, help="The organization that contains the repo."),
                 validation_func=lookup_real_org, validation_func_kwargs={}),
            dict(name="repo", properties=dict(type=str, help="The name of the repo to set the topics on."),
                 lowercase=False, validation_func=extract_repo_name, validation_func_kwargs={}),

        ],
        optional=[
            dict(name="topics", properties=dict(nargs="?", default="", type=str,
                                                help="A comma separated list of topics to set on a repo. If"
                                                     " omitted, this will clear out the topics. "
                                                     "Note: This will replace all existing topics."))
        ]
    )
    @auth()
    def set_repo_topics_command(self, data, user_data, org, repo, topics):
        # Make the topics a list:
        if topics == "":
            topic_list = []
        else:
            topic_list = topics.split(",")

        # Output that we are doing work:
        send_info(data["channel"], "@{}: Working, Please wait...".format(user_data["name"]), thread=data["ts"])

        # Set the topics:
        if self.set_repo_topics(data, user_data, org, repo, topic_list):
            # Done:
            if len(topic_list) == 0:
                send_success(data["channel"],
                             "@{}: The repo: {repo}'s topics were cleared.".format(user_data["name"], repo=repo),
                             markdown=True, thread=data["ts"])

            else:
                send_success(data["channel"],
                             "@{}: The topics: `{topics}` were applied "
                             "to the repo: {repo}".format(user_data["name"], topics=", ".join(topic_list), repo=repo),
                             markdown=True, thread=data["ts"])

    def check_if_repo_exists(self, data, user_data, reponame, real_org):
        try:
            result = self.check_gh_for_existing_repo(reponame, real_org)

            if not result:
                send_error(data["channel"],
                           "@{}: This repository does not exist in {}.".format(user_data["name"], real_org),
                           thread=data["ts"])
                return False

            return True

        except Exception as e:
            send_error(data["channel"],
                       "@{}: I encountered a problem:\n\n{}".format(user_data["name"], e), thread=data["ts"])
            return False

    def make_repo_edit(self, data, user_data, reponame, real_org, **kwargs):
        try:
            self.modify_repo(reponame, real_org, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered modifying the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered setting the {} field.\n"
                       "Here are the details: {}".format(kwargs.keys()[0], user_data["name"], str(e)),
                       thread=data["ts"])
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
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])
            return False

    def set_repo_topics(self, data, user_data, reponame, real_org, topics, **kwargs):
        try:
            return self.set_repo_topics_http(reponame, real_org, topics, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while setting topics to the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])
            return False

    def get_repo_deploy_keys(self, data, user_data, reponame, real_org, **kwargs):
        try:
            return self.get_repo_deploy_keys_http(reponame, real_org, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while getting deploy keys from the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])

    def get_repo_deploy_key_by_id(self, data, user_data, reponame, real_org, deploy_key_id, **kwargs):
        try:
            return self.get_repo_deploy_key_by_id_http(reponame, real_org, deploy_key_id, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while getting deploy key from the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])

        return False

    def add_repo_deploy_key(self, data, user_data, reponame, real_org, title, deploy_key, readonly, **kwargs):
        try:
            return self.add_repo_deploy_key_http(reponame, real_org, title, deploy_key, readonly, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while adding deploy key to the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])
            return False

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])

    def delete_repo_deploy_key(self, data, user_data, reponame, real_org, key_id, **kwargs):
        try:
            return self.delete_repo_deploy_key_http(reponame, real_org, key_id, **kwargs)

        except requests.exceptions.RequestException as re:
            send_error(data["channel"],
                       "@{}: Problem encountered while deleting deploy key to the repository.\n"
                       "The response code from GitHub was: {}".format(user_data["name"], str(re)), thread=data["ts"])

        except Exception as e:
            send_error(data["channel"],
                       "@{}: Problem encountered while parsing the response.\n"
                       "Here are the details: {}".format(user_data["name"], str(e)), thread=data["ts"])

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

    def set_repo_topics_http(self, org, repo, topics, **kwargs):
        """
        Set topics on a repo.
        See: https://developer.github.com/v3/repos/#replace-all-topics-for-a-repository
        :param org:
        :param repo:
        :param topics:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': "application/vnd.github.mercy-preview+json"
        }

        data = {"names": topics}

        api_part = 'repos/{}/{}/topics'.format(org, repo)

        response = requests.put('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data),
                                headers=headers, timeout=10)

        if response.status_code != 200:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

        return True

    def add_outside_collab_to_repo(self, outside_collab_id, repo_name, real_org, permission):
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        data = {"permission": permission}

        # Add the outside collab to the repo:
        api_part = 'repos/{}/{}/collaborators/{}'.format(real_org, repo_name, outside_collab_id)
        response = requests.put('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data), headers=headers, timeout=10)

        # GitHub response code flakiness...
        if response.status_code not in [201, 204]:
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

        # GitHub response code flakiness...
        if response.status_code not in [201, 204]:
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

        # GitHub response code flakiness...
        if response.status_code not in [201, 204]:
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

        response = requests.patch('{}{}'.format(GITHUB_URL, api_part), data=json.dumps(data), headers=headers,
                                  timeout=10)

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

        # Get all teams inside the organization:
        api_part = 'orgs/{}/teams'.format(org)
        url = '{}{}'.format(GITHUB_URL, api_part)

        while True:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                raise ValueError("GitHub Problem: Could not list teams -- received error code: {}"
                                 .format(response.status_code))

            # Check if the provided team_name belongs to a team inside the organization:
            for x in response.json():
                if x["slug"] == team_name:
                    return x["id"]

            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                return False

    def get_repo_deploy_keys_http(self, repo, org, **kwargs):
        """
        List deploy keys associated with a repo.

        :param repo:
        :param org:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        api_part = 'repos/{}/{}/keys'.format(org, repo)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def get_repo_deploy_key_by_id_http(self, repo, org, deploy_key_id, **kwargs):
        """
        List deploy keys associated with a repo.

        :param repo:
        :param org:
        :param deploy_key_id:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        api_part = 'repos/{}/{}/keys/{}'.format(org, repo, deploy_key_id)

        response = requests.get('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return

        else:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def add_repo_deploy_key_http(self, repo, org, title, deploy_key, readonly, **kwargs):
        """
        List deploy keys associated with a repo.

        :param repo:
        :param org:
        :param title:
        :param deploy_key:
        :param readonly:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        api_part = 'repos/{}/{}/keys'.format(org, repo)

        data = {
            "title": title,
            "key": deploy_key,
            "read_only": readonly
        }

        response = requests.post(
            '{}{}'.format(GITHUB_URL, api_part),
            data=json.dumps(data),
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            return response.json()
        elif response.status_code == 422:
            # Deploy key is invalid
            return False
        else:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)

    def delete_repo_deploy_key_http(self, repo, org, key_id, **kwargs):
        """
        List deploy keys associated with a repo.

        :param repo:
        :param org:
        :param key_id:
        :param kwargs:
        :return:
        """
        headers = {
            'Authorization': 'token {}'.format(self.token),
            'Accept': GITHUB_VERSION
        }

        api_part = 'repos/{}/{}/keys/{}'.format(org, repo, key_id)

        response = requests.delete('{}{}'.format(GITHUB_URL, api_part), headers=headers, timeout=10)

        if response.status_code == 204:
            return True
        else:
            message = 'An error was encountered communicating with GitHub: Status Code: {}' \
                .format(response.status_code)
            raise requests.exceptions.RequestException(message)
