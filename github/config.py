from ..auth_plugins.enabled_plugins import AUTH_PLUGINS

# Define the organizations that this Bot will examine.
ORGS = {
    "Real_Org_Name_here": {
        "aliases": [
            "some_alias_for_your_org_here"
        ],
        "public_only": False,   # False means that your org supports Private repos, True otherwise.
        "new_repo_teams": [  # This is a list, so add all the teams you want to here...
            {
                "id": "0000000",        # The team ID for the team that you want new repos to be attached to
                "perm": "push",         # The permission, either "push", "pull", or "admin"...
                "name": "TeamName"      # The name of the team here...
            }
        ]
    }
}

# github API Version
GITHUB_VERSION = "application/vnd.github.v3+json"   # Is this still needed?

# GITHUB API PATH:
GITHUB_URL = "https://api.github.com/"

# You can use this to add/replace fields from the command_plugins dictionary:
USER_COMMAND_DICT = {
    # This is an example for enabling Duo 2FA support for the "!SetDefaultBranch" command:
    # "!SetDefaultBranch": {
        # "auth": {
        #    "plugin": AUTH_PLUGINS["duo"],
        #    "kwargs": {}
        # }
    #}
}
