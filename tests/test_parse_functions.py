import pytest


def test_preformat_args():
    from hubcommander.bot_components.parse_functions import preformat_args
    test_string = "!TheCommand [argOne] {argTwo}"
    result = preformat_args(test_string)
    assert len(result) == 2
    assert result[0] == "argone"
    assert result[1] == "argtwo"


def test_preformat_args_with_spaces():
    from hubcommander.bot_components.parse_functions import preformat_args_with_spaces
    test_string = "!TheCommand [argOne] {argTwo} “argThree” \"argFour\" \"argFive\""
    result = preformat_args_with_spaces(test_string, 3)
    assert len(result) == 5
    assert result[0] == "argone"
    assert result[1] == "argtwo"
    assert result[2] == "argThree"
    assert result[3] == "argFour"
    assert result[4] == "argFive"

    test_string_two = "!SetDescription Netflix HubCommander \"A Slack bot for GitHub ‘management’\""
    result = preformat_args_with_spaces(test_string_two, 1)
    assert len(result) == 3
    assert result[2] == "A Slack bot for GitHub 'management'"

    test_failures = [
        "!SomeCommand \"only one quote",
        "!SomeCommand \"three quotes\"\"",
        "!SomeCommand no quotes",
    ]
    for tf in test_failures:
        with pytest.raises(SystemExit):
            preformat_args_with_spaces(tf, 1)

    # Failure with incorrect number of quoted params:
    with pytest.raises(SystemExit):
        preformat_args_with_spaces(test_string_two, 3)


def test_extract_repo_name():
    from hubcommander.bot_components.parse_functions import extract_repo_name
    test_strings = {
        "www.foo.com": "<http://www.foo.com|www.foo.com>",
        "foo": "foo",
        "HubCommander": "HubCommander",
        "netflix.github.io": "<https://netflix.github.io|netflix.github.io>"
    }

    for repo, uri in test_strings.items():
        assert extract_repo_name(None, uri) == repo


def test_parse_toggles():
    from hubcommander.bot_components.parse_functions import parse_toggles, TOGGLE_ON_VALUES, \
        TOGGLE_OFF_VALUES, ParseException

    for toggle in TOGGLE_ON_VALUES:
        assert parse_toggles(None, toggle)

    for toggle in TOGGLE_OFF_VALUES:
        assert not parse_toggles(None, toggle)

    with pytest.raises(ParseException):
        parse_toggles(None, "NotAProperToggle")
