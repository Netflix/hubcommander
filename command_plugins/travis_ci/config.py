from hubcommander.auth_plugins.enabled_plugins import AUTH_PLUGINS

USER_AGENT = "YOUR_USER_AGENT_FOR_TRAVIS_CI_HERE"

# Define the organizations which Travis is enabled on:
# This is largely a copy and paste from the GitHub plugin config
ORGS = {
    "Real_Org_Name_here": {
        "aliases": [
            "some_alias_for_your_org_here"
        ]
    }
}

USER_COMMAND_DICT = {
    # This is an example for enabling Duo 2FA support for the "!EnableTravis" command:
    # "!EnableTravis": {
        # "auth": {
        #    "plugin": AUTH_PLUGINS["duo"],
        #    "kwargs": {}
        # }
    # }
}
