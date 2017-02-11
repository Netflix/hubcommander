"""
.. module: hubcommander.tests.test_fixtures
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""


def test_slack_client(slack_client):
    # Test the "say" method to ensure that the Slack client is working...
    import hubcommander.bot_components
    assert hubcommander.bot_components.SLACK_CLIENT == slack_client
