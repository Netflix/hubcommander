Travis CI Plugin
=================

The [Travis CI](https://travis-ci.org/) plugin features an `!EnableTravis` command which will enable Travis CI 
on a given repository. By default, this plugin is disabled.

This plugin makes an assumption that you have Travis CI Public (for public repos) and 
Professional (for private repos) enabled for your GitHub organizations.

This plugin will automatically detect which Travis CI (Public vs. Pro) to use based on the public/private 
visibility of a given GitHub repository.

How does it work?
----------------
The Travis CI plugin operates similarly to the GitHub plugin in that it brokers privileged commands
via a simple tool. This is necessary, because enabling Travis CI on an repository [requires administrative
permissions](https://docs.travis-ci.com/user/getting-started#To-get-started-with-Travis-CI%3A)
for a given repository.

As such, this plugin is only effective if you utilize Travis CI credentials with the GitHub user account
shared by the GitHub plugin.

This plugin works by first fetching details about the repository from GitHub. The plugin will then
have Travis CI synchronize with GitHub so it can see the repository. Once synchronized, it will
then run the API command to enable Travis CI on the repo.

Configuration
-------------
This plugin requires access to the Travis CI API version 3 
([currently in closed BETA](https://developer.travis-ci.org/)). You must contact Travis CI's support 
and request a GitHub ID to be added into the beta for access to the methods utilized by this plugin. 

Once you are added into the closed beta, you will need to get your Travis CI tokens. These tokens
are _different_ for public and professional Travis CI.

### GitHub API Token for Travis

You must create a GitHub API token first. This is used to fetch the Travis CI tokens. You must
create a personal access token to with the following scopes:

   - `repo` (All)
   - `read:org`
   - `write:repo_hook`
   - `read:repo_hook`
   - `user:email`
   
Keep the generated token in a safe place for the time being. You only need token for the
next section -- after that, you shouldn't need the token stored anywhere. However, don't
delete the generated key on GitHub.

### Get Travis CI Credentials
You need to obtain the following 6 items:
   - `TRAVIS_PRO_USER`: This is the name of the GitHub user name running the Travis CI (Pro) commands
   - `TRAVIS_PRO_ID`: The Travis CI Pro ID of the GitHub user (see below)
   - `TRAVIS_PRO_TOKEN`: The Travis CI Pro Token (see below)
   - `TRAVIS_PUBLIC_USER`: This is the name of the GitHub user name running the Travis CI (Public) commands
   - `TRAVIS_PUBLIC_ID`: The Travis CI Public ID of the GitHub user (see below)
   - `TRAVIS_PUBLIC_TOKEN`: The Travis CI Public Token (see below)

The 6 fields above will need to be added into the bot secrets `dict` and encrypted.

#### Fetch Travis CI Tokens
You must follow the instructions [here](https://docs.travis-ci.com/api#authentication) to obtain the
Travis CI credentials. *Note: you must do this TWICE, once for `.org` (public) and again for
`.com` (professional) to get all the required tokens.*

#### Fetch Travis CI IDs
Once you fetch the tokens, you will also need to fetch your Travis CI ID for both public
and pro. You do this by executing the 
[Travis CI `user` API](https://developer.travis-ci.org/explore/user) to fetch the `id`. 
(Again, this needs to be run twice, for Public and Pro.)

#### Update the credentials dictionary
You must update the credentials dictionary that is used on the startup of the bot.
The fields are specified above.

#### Define the GitHub organizations to enable Travis CI on
In the Travis CI plugin's [configuration file](https://github.com/Netflix/hubcommander/blob/master/command_plugins/travis_ci/config.py), there is an `ORGS` `dict`.
This is very similar in nature to the `ORGS` `dict` that exists in the GitHub plugin's configuration file. This
`dict` defines the GitHub Organizations that Travis CI is enabled on, and the corresponding aliases for those orgs.

#### Define the Travis CI User Agent
This can be anything of your choosing. Make sure that you set the `USER_AGENT` variable in the Travis CI plugin's config file.

### Enable the plugin
To enable the plugin, uncomment the `import` statement in 
[`command_plugins/enabled_plugins.py`](https://github.com/Netflix/hubcommander/blob/master/command_plugins/enabled_plugins.py)

Then, uncomment the `#"travisci": TravisPlugin(),` entry in the `COMMAND_PLUGINS` `dict`.

Restart the bot, and you should see output on app startup for the `travisci` plugin being enabled.
