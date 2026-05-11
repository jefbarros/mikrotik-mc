import pytest

from src.commands import READ_ONLY_COMMANDS, validate_all_commands, validate_command
from src.exceptions import CommandValidationError


def test_allowlisted_commands_pass():
    validate_all_commands()
    for command in READ_ONLY_COMMANDS:
        assert validate_command(command) == " ".join(command.split())


@pytest.mark.parametrize(
    "command",
    [
        "/ip address add address=1.2.3.4/32 interface=ether1",
        "/ip address set 0 disabled=yes",
        "/ip firewall filter remove 0",
        "/system backup save name=test",
        "/export show-sensitive",
        "/export file=config",
    ],
)
def test_dangerous_or_unknown_commands_are_blocked(command):
    with pytest.raises(CommandValidationError):
        validate_command(command)


def test_export_terse_is_allowed():
    assert validate_command("/export terse") == "/export terse"

