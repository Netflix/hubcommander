"""
Use this file to initialize all command plugins.

The "setup" method will be executed by hubcommander on startup.
"""
from hubcommander.command_plugins.github.plugin import GitHubPlugin
#from hubcommander.command_plugins.travis_ci.plugin import TravisPlugin
#from hubcommander.command_plugins.repeat.plugin import RepeatPlugin

COMMAND_PLUGINS = {
    "github": GitHubPlugin(),
    #"travisci": TravisPlugin(),
    #"repeat": RepeatPlugin(),
}
