"""
.. module: hubcommander.bot_components.parse_functions
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""

TOGGLE_ON_VALUES = ["on", "true", "enabled"]
TOGGLE_OFF_VALUES = ["off", "false", "disabled"]


class ParseException(Exception):
    """
    Exception specific to parsing logic, where improper data was fed in.
    """
    def __init__(self, arg_type, proper_values):
        super(ParseException, self).__init__("Parse Error")

        self.arg_type = arg_type
        self.proper_values = proper_values

    def format_proper_usage(self, user):
        usage_text = "@{user}: Invalid argument passed for `{arg_type}`.\n\n" \
                     "{proper_values}"

        return usage_text.format(user=user, arg_type=self.arg_type, proper_values=self.proper_values)


def preformat_args(text):
    return text.lower() \
               .replace('[', '').replace(']', '') \
               .replace('{', '').replace('}', '') \
               .split(" ")[1:]


def preformat_args_with_spaces(text, num_quoted):
    """
    This method will not only strip out the things that need to be stripped out, but it will also
    ensure that double-quoted objects are extracted as independent arguments.

    For example, if the text passed in was:
    !SetDescription Netflix HubCommander "A Slack bot for GitHub management", we would want to get back:
    a list that contains: ["netflix", "hubcommander", '"A Slack bot for GitHub management"']

    The `num_quoted` param refers to the number of double-quoted parameters are required for the command.
    For the example above, there is one double-quoted parameter required for the command.

    :param text:
    :param num_quoted:
    :return:
    """
    working = text.replace('[', '').replace(']', '') \
        .replace('{', '').replace('}', '') \
        .replace(u'\u201C', "\"").replace(u'\u201D', "\"") \
        .replace(u'\u2018', "\'").replace(u'\u2019', "\'")  # macOS's Bullshit around quotes..

    # Check if there are 0 or an un-even number of quotation marks.  If so, then exit:
    if working.count('\"') < 2:
        raise SystemExit()

    if working.count('\"') % 2 != 0:
        raise SystemExit()

    # Get all the quoted things: (We only really care about the double-quotes, since they are related to command
    # syntax.)
    quotes = working.split('"')[1::2]
    if len(quotes) != num_quoted:
        raise SystemExit()

    # Remove them from the working string:
    working = working.replace("\"", '')

    for quote in quotes:
        working = working.replace(quote, '')

    # Get the space delimited commands:
    working = working.lower()

    # Remove extra dangling whitespaces (there must be 1 dangling space at the end for the split operation to operate):
    if num_quoted > 1:
        working = working[0:-(num_quoted - 1)]

    space_delimited = working.split(" ")[1:-1]
    # The -1 above is needed, because there will be additional empty items on the list due to the space
    # after the other positional arguments :/

    return space_delimited + quotes


def extract_repo_name(reponame, **kwargs):
    """
    Reponames can be FQDN's. Slack has an annoying habit of sending over URL's like so:
    <http://www.foo.com|www.foo.com>
    ^^ Need to pull out the URL. In our case, we care only about the label, which is the last part between | and >
    :param reponame:
    :return:
    """
    if "|" not in reponame:
        return reponame

    split_repo = reponame.split("|")[1]

    return split_repo.replace(">", "")


def parse_toggles(toggle, toggle_type="toggle", **kwargs):
    """
    Parses typical toggle values, like off, on, enabled, disabled, true, false, etc.
    :param toggle_type:
    :param toggle:
    :return:
    """
    toggle = toggle.lower()

    if toggle in TOGGLE_ON_VALUES:
        return True

    elif toggle in TOGGLE_OFF_VALUES:
        return False

    raise ParseException(toggle_type, "Acceptable values are: `{on}, {off}`".format(
        on=", ".join(TOGGLE_ON_VALUES), off=", ".join(TOGGLE_OFF_VALUES)
    ))
