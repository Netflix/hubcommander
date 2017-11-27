"""
.. module: hubcommander.github.plugin.decorators
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from hubcommander.bot_components.slack_comm import send_error


def repo_must_exist(org_arg="org"):
    def command_decorator(func):
        def decorated_command(github_plugin, data, user_data, *args, **kwargs):
            # Just 1 repo -- or multiple?
            if kwargs.get("repo"):
                repos = [kwargs["repo"]]
            else:
                repos = kwargs["repos"]

            # Check if the specified GitHub repo exists:
            for repo in repos:
                if not github_plugin.check_if_repo_exists(data, user_data, repo, kwargs[org_arg]):
                    return

            # Run the next function:
            return func(github_plugin, data, user_data, *args, **kwargs)

        return decorated_command

    return command_decorator


def team_must_exist(org_arg="org", team_arg="team"):
    def command_decorator(func):
        def decorated_command(github_plugin, data, user_data, *args, **kwargs):
            # Check if the specified GitHub team exists:
            kwargs['team_id'] = github_plugin.find_team_id_by_name(kwargs[org_arg], kwargs[team_arg])
            if not kwargs.get("team_id"):
                send_error(data["channel"], "@{}: The GitHub team: {} does not exist.".format(user_data["name"],
                                                                                              kwargs[team_arg]),
                           thread=data["ts"])
                return
            # Run the next function:
            return func(github_plugin, data, user_data, *args, **kwargs)

        return decorated_command

    return command_decorator


def github_user_exists(user_arg):
    def command_decorator(func):
        def decorated_command(github_plugin, data, user_data, *args, **kwargs):
            # Check if the given GitHub user actually exists:
            try:
                found_user = github_plugin.get_github_user(kwargs[user_arg])

                if not found_user:
                    send_error(data["channel"], "@{}: The GitHub user: {} does not exist.".format(user_data["name"],
                                                                                                  kwargs[user_arg]),
                               thread=data["ts"])
                    return

            except Exception as e:
                send_error(data["channel"],
                           "@{}: A problem was encountered communicating with GitHub to verify the user's GitHub "
                           "id. Here are the details:\n{}".format(user_data["name"], str(e)),
                           thread=data["ts"])
                return

            # Run the next function:
            return func(github_plugin, data, user_data, *args, **kwargs)

        return decorated_command

    return command_decorator


def branch_must_exist(repo_arg="repo", org_arg="org", branch_arg="branch"):
    """
    This should be placed AFTER the `@repo_must_exist()` decorator.
    :param repo_arg:
    :param org_arg:
    :param branch_arg:
    :param kwargs:
    :return:
    """
    def command_decorator(func):
        def decorated_command(github_plugin, data, user_data, *args, **kwargs):
            # Check if the branch exists on the repo....
            if not (github_plugin.check_for_repo_branch(kwargs[repo_arg], kwargs[org_arg], kwargs[branch_arg])):
                send_error(data["channel"],
                           "@{}: This repository does not have the branch: `{}`.".format(user_data["name"],
                                                                                         kwargs[branch_arg]),
                           markdown=True, thread=data["ts"])
                return

            # Run the next function:
            return func(github_plugin, data, user_data, *args, **kwargs)

        return decorated_command

    return command_decorator
