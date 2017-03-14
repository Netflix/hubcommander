"""
Use this file to initialize all command plugins.

The "setup" method will be executed by hubcommander on startup.
"""
# from hubcommander.command_plugins.travis_ci.plugin import TravisPlugin
from hubcommander.github.plugin import GitHubPlugin

GITHUB_PLUGIN = GitHubPlugin()

COMMAND_PLUGINS = {
    #"travisci": TravisPlugin(),
}
