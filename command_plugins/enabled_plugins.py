"""
Use this file to initialize all command plugins.

The "setup" method will be executed by hubcommander on startup.
"""
# from command_plugins.travis_ci.plugin import TravisPlugin
from github.plugin import GitHubPlugin

GITHUB_PLUGIN = GitHubPlugin()

COMMAND_PLUGINS = {
    #"travisci": TravisPlugin(),
}
