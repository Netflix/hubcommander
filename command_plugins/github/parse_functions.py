"""
.. module: hubcommander.github.plugin.parse_functions
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import validators
from hubcommander.bot_components.parse_functions import ParseException


def lookup_real_org(plugin_obj, org, **kwargs):
    try:
        return plugin_obj.org_lookup[org.lower()][0]
    except KeyError as _:
        raise ParseException("org", "Invalid org name sent in. Run `!ListOrgs` to see the valid orgs.")


def extract_url(plugin_obj, url, **kwargs):
    if "|" in url:
        url = url.split("|")[0]

    return url.replace("<", "").replace(">", "")


def validate_homepage(plugin_obj, homepage, **kwargs):
    url = extract_url(plugin_obj, homepage)

    if url != "":
        if not validators.url(url):
            raise ParseException("homepage", "Invalid homepage URL was sent in. It must be a well formed URL.")

    return url
