import json

from hubcommander.bot_components.decorators import hubcommander_command, format_help_text, auth
from hubcommander.bot_components.slack_comm import WORKING_COLOR
from hubcommander.bot_components.parse_functions import ParseException


def test_hubcommander_command_required(user_data, slack_client):
    fail_command_kwargs = dict(
        name="!FailCommand",
        usage="!FailCommand <arg1>",
        description="This is a test command that will fail due to lack of required args",
        required=[
            dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
        ],
        optional=[]
    )

    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(
            name="!TestCommand",
            usage="!TestCommand <arg1> <arg2> <arg3>",
            description="This is a test command to make sure that things are working properly.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
                dict(name="arg2", properties=dict(type=str, help="This is argument 2")),
                dict(name="arg3", properties=dict(type=str, help="This is argument 3"))
            ],
            optional=[]
        )
        def pass_command(self, data, user_data, arg1, arg2, arg3):
            assert self
            assert data
            assert user_data
            assert arg1 == "arg1"
            assert arg2 == "arg2"
            assert arg3 == "arg3"

        @hubcommander_command(**fail_command_kwargs)
        def fail_command(self, data, user_data, arg1):
            assert False  # Can't Touch This...

    tc = TestCommands()

    data = dict(text="!TestCommand arg1 arg2 arg3")
    tc.pass_command(data, user_data)

    data = dict(text="!FailCommand", channel="12345")
    tc.fail_command(data, user_data)

    help_text = format_help_text(data, user_data, **fail_command_kwargs)
    attachment = {
        "text": help_text,
        "color": WORKING_COLOR,
        "mrkdwn_in": ["text"]
    }
    slack_client.api_call.assert_called_with("chat.postEphemeral", channel="12345", as_user=True,
                                             attachments=json.dumps([attachment]), text=" ", user=user_data["id"])


def test_hubcommander_command_optional(user_data, slack_client):
    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(
            name="!OptionalArgs",
            usage="!OptionalArgs <arg1> <optional arg here> <another optional argument here>",
            description="This is a test command with an optional argument",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
            ],
            optional=[
                dict(name="--optional", properties=dict(type=str, help="This is argument 2")),
                dict(name="--optional2", properties=dict(type=str, help="This is argument 3")),
                dict(name="--optional3", properties=dict(type=str, help="This is argument 4"))
            ]
        )
        def optional_arg_command(self, data, user_data, arg1, **optionals):
            assert arg1 == "required"
            assert len(optionals) == 3
            assert optionals["optional"] == "some_optional"
            assert optionals["optional2"] == "some_optional2"
            assert not optionals["optional3"]

    tc = TestCommands()

    data = dict(text="!OptionalArgs required --optional some_optional --optional2 some_optional2")
    tc.optional_arg_command(data, user_data)


def test_hubcommander_command_with_custom_validation(user_data, slack_client):
    from hubcommander.bot_components.parse_functions import parse_toggles

    verify_command_kwargs = dict(
        name="!VerifyToggle",
        usage="!VerifyToggle <testToggle>",
        description="This is a test command to verify proper toggles",
        required=[
            dict(name="test_toggle", properties=dict(type=str, help="This is argument 1"),
                 validation_func=parse_toggles,
                 validation_func_kwargs=dict(
                     toggle_type="<enablement flag>"
                 ))
        ]
    )

    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(**verify_command_kwargs)
        def verify_toggle(self, data, user_data, test_toggle):
            assert type(test_toggle) is bool

    tc = TestCommands()

    data = dict(text="!VerifyToggle on")
    tc.verify_toggle(data, user_data)

    data = dict(text="!VerifyToggle false")
    tc.verify_toggle(data, user_data)

    data = dict(text="!VerifyToggle WillFail", channel="12345")
    tc.verify_toggle(data, user_data)

    proper_usage_text = ""
    try:
        parse_toggles(tc, "WillFail", toggle_type="<enablement flag>")
    except ParseException as pe:
        proper_usage_text = pe.format_proper_usage(user_data["name"])

    attachment = {
        "text": proper_usage_text,
        "color": "danger",
        "mrkdwn_in": ["text"]
    }
    slack_client.api_call.assert_called_with("chat.postEphemeral", channel="12345", as_user=True,
                                             attachments=json.dumps([attachment]), text=" ", user=user_data["id"])


def test_auth_decorator(user_data, slack_client, auth_plugin):
    class TestCommands:
        def __init__(self):
            self.commands = {
                "!TestCommand": {
                    "auth": {
                        "plugin": auth_plugin,
                        "kwargs": {
                            "should_auth": True
                        }
                    }
                },
                "!TestCommand2": {
                    "auth": {
                        "plugin": auth_plugin,
                        "kwargs": {
                            "should_auth": False
                        }
                    }
                },
                "!OptionalArgs": {
                    "auth": {
                        "plugin": auth_plugin,
                        "kwargs": {
                            "should_auth": True
                        }
                    }
                },
                "!OptionalArgs2": {
                    "auth": {
                        "plugin": auth_plugin,
                        "kwargs": {
                            "should_auth": False
                        }
                    }
                }
            }

        @hubcommander_command(
            name="!TestCommand",
            usage="!TestCommand <arg1> <arg2> <arg3>",
            description="This is a test command to make sure that things are working properly.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
                dict(name="arg2", properties=dict(type=str, help="This is argument 2")),
                dict(name="arg3", properties=dict(type=str, help="This is argument 3"))
            ],
            optional=[]
        )
        @auth()
        def pass_command(self, data, user_data, arg1, arg2, arg3):
            assert arg1 == "arg1"
            assert arg2 == "arg2"
            assert arg3 == "arg3"
            return True

        @hubcommander_command(
            name="!TestCommand2",
            usage="!TestCommand2 <arg1> <arg2> <arg3>",
            description="This is a test command that will fail to authenticate.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
                dict(name="arg2", properties=dict(type=str, help="This is argument 2")),
                dict(name="arg3", properties=dict(type=str, help="This is argument 3"))
            ],
            optional=[]
        )
        @auth()
        def fail_command(self, data, user_data, arg1, arg2, arg3):
            # Will never get here...
            assert False

        @hubcommander_command(
            name="!OptionalArgs",
            usage="!OptionalArgs <arg1> <optional arg here> <another optional argument here>",
            description="This is a test command with an optional argument",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
            ],
            optional=[
                dict(name="--optional", properties=dict(type=str, help="This is argument 2")),
                dict(name="--optional2", properties=dict(type=str, help="This is argument 3")),
                dict(name="--optional3", properties=dict(type=str, help="This is argument 4"))
            ]
        )
        @auth()
        def optional_arg_command(self, data, user_data, arg1, **optionals):
            assert arg1 == "required"
            assert len(optionals) == 3
            assert optionals["optional"] == "some_optional"
            assert optionals["optional2"] == "some_optional2"
            assert not optionals["optional3"]
            return True

        @hubcommander_command(
            name="!OptionalArgs2",
            usage="!OptionalArgs2 <arg1> <optional arg here> <another optional argument here>",
            description="This is a test command with an optional argument that will fail to auth",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This is argument 1")),
            ],
            optional=[
                dict(name="--optional", properties=dict(type=str, help="This is argument 2")),
                dict(name="--optional2", properties=dict(type=str, help="This is argument 3")),
                dict(name="--optional3", properties=dict(type=str, help="This is argument 4"))
            ]
        )
        @auth()
        def optional_fail_arg_command(self, data, user_data, arg1, **optionals):
            # Will never reach this:
            assert False

    tc = TestCommands()
    data = dict(text="!TestCommand arg1 arg2 arg3")
    assert tc.pass_command(data, user_data)
    assert not tc.fail_command(data, user_data)

    # Test that commands with optional arguments work properly:
    data = dict(text="!OptionalArgs required --optional some_optional --optional2 some_optional2")
    assert tc.optional_arg_command(data, user_data)
    assert not tc.optional_fail_arg_command(data, user_data)


def test_help_command_with_list(user_data, slack_client):
    valid_values = ["one", "two", "three"]

    verify_command_kwargs = dict(
        name="!TestCommand",
        usage="!TestCommand <testThing>",
        description="This is a test command to test help text for things in lists",
        required=[
            dict(name="test_thing", properties=dict(type=str.lower, help="Must be one of: `{values}`"),
                 choices="valid_values")
        ]
    )

    class TestCommands:
        def __init__(self):
            self.commands = {
                "!TestCommand": {
                    "valid_values": valid_values
                }
            }

        @hubcommander_command(**verify_command_kwargs)
        def the_command(self, data, user_data, test_thing):
            assert True

    tc = TestCommands()

    # Will assert True
    data = dict(text="!TestCommand one")
    tc.the_command(data, user_data)

    # Will ALSO assert True... we are making sure to lowercase the choices with str.lower as the type:
    data = dict(text="!TestCommand ThReE")
    tc.the_command(data, user_data)

    # Will NOT assert true -- this will output help text:
    data = dict(text="!TestCommand", channel="12345")
    tc.the_command(data, user_data)

    help_text = format_help_text(data, user_data, **verify_command_kwargs)
    attachment = {
        "text": help_text,
        "color": WORKING_COLOR,
        "mrkdwn_in": ["text"]
    }
    slack_client.api_call.assert_called_with("chat.postEphemeral", channel="12345", as_user=True,
                                             attachments=json.dumps([attachment]), text=" ", user=user_data["id"])

    # Will NOT assert true
    data = dict(text="!TestCommand alskjfasdlkf", channel="12345")
    tc.the_command(data, user_data)
    attachment = {
        "text": help_text,
        "color": WORKING_COLOR,
        "mrkdwn_in": ["text"]
    }
    slack_client.api_call.assert_called_with("chat.postEphemeral", channel="12345", as_user=True,
                                             attachments=json.dumps([attachment]), text=" ", user=user_data["id"])


def test_uppercase_and_lowercasing(user_data, slack_client):
    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(
            name="!TestCommand",
            usage="!TestCommand <arg1> <arg2> <arg3>",
            description="This is a test command to make sure that casing is correct.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="NoT AlL LoWeRCaSE"),
                     lowercase=False),
                dict(name="arg2", properties=dict(type=str, help="all lowercase")),
                dict(name="arg3", properties=dict(type=str, help="ALL UPPERCASE"),
                     uppercase=True)
            ],
        )
        def pass_command(self, data, user_data, arg1, arg2, arg3):
            assert self
            assert data
            assert user_data
            assert arg1 == "NoT AlL LoWeRCaSE"
            assert arg2 == "all lowercase"
            assert arg3 == "ALL UPPERCASE"

    tc = TestCommands()

    data = dict(text="!TestCommand \"NoT AlL LoWeRCaSE\" \"ALL lOWERcASE\" \"all Uppercase\"")
    tc.pass_command(data, user_data)


def test_cleanup(user_data, slack_client):
    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(
            name="!TestCommand",
            usage="!TestCommand <arg1> <arg2>",
            description="This is a test command to make sure that undesirable characters are cleaned up.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="This will clean things up")),
                dict(name="arg2", properties=dict(type=str, help="This will not clean things up."),
                     cleanup=False),
            ],
        )
        def pass_command(self, data, user_data, arg1, arg2):
            assert self
            assert data
            assert user_data
            assert arg1 == "all cleaned up!"
            assert arg2 == "<not all[} cleaned up}"

    tc = TestCommands()

    data = dict(text="!TestCommand \"<all cleaned up!>>][\" \"<not all[} cleaned up}\"")
    tc.pass_command(data, user_data)

def test_auth_token_passed_through(user_data, slack_client):
    class TestCommands:
        def __init__(self):
            pass

        @hubcommander_command(
            name="!TestCommand",
            usage="!TestCommand <arg1>",
            description="This is a test command to make sure that undesirable characters are cleaned up.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="some arg")),
            ],
        )
        def pass_command(self, data, user_data, arg1):
            assert self
            assert data
            assert data['auth_token'] == 'the_auth_token'
            assert arg1 == "myval"

        @hubcommander_command(
            name="!OtherCommand",
            usage="!OtherCommand <arg1>",
            description="This is a test command to make sure that auth_token is optional.",
            required=[
                dict(name="arg1", properties=dict(type=str, help="some arg")),
            ],
        )
        def noauth_token_command(self, data, user_data, arg1):
            assert self
            assert data
            assert data['auth_token'] is None
            assert arg1 == "myval"

    tc = TestCommands()

    data = dict(text="!TestCommand myval --auth_token=the_auth_token")
    tc.pass_command(data, user_data)

    data = dict(text="!TestCommand --auth_token=the_auth_token myval")
    tc.pass_command(data, user_data)

    data = dict(text="!OtherCommand myval")
    tc.noauth_token_command(data, user_data)
