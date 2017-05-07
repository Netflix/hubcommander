"""
.. module: hubcommander.bot_components.bot_classes
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""


class BotPlugin:
    def __init__(self):
        pass

    def setup(self, secrets, **kwargs):
        raise NotImplementedError()


class BotCommander(BotPlugin):
    def __init__(self):
        super().__init__()
        self.commands = {}

    def setup(self, secrets, **kwargs):
        pass


class BotAuthPlugin(BotPlugin):
    def __init__(self):
        super().__init__()

    def setup(self, secrets, **kwargs):
        pass

    def authenticate(self, *args, **kwargs):
        raise NotImplementedError()
