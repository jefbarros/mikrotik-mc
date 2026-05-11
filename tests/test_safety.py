import pytest

from src.exceptions import SafetyError
from src.safety import validate_provisioning_command, validate_routeros_script


@pytest.mark.parametrize(
    "script",
    [
        "/system reset-configuration",
        "/system reboot",
        "/system shutdown",
        "/system backup save name=x",
        "/import file=x.rsc",
        "/tool fetch url=http://example.com",
        "/certificate export-certificate x",
        "/export show-sensitive",
    ],
)
def test_forbidden_commands_are_blocked(script):
    with pytest.raises(SafetyError):
        validate_routeros_script(script, allow_sensitive_password=True)


def test_versionable_script_cannot_contain_password():
    with pytest.raises(SafetyError):
        validate_routeros_script('/user add name=x password="secret"', allow_sensitive_password=False)


def test_provisioning_command_must_be_absolute():
    with pytest.raises(SafetyError):
        validate_provisioning_command("ip address add address=1.1.1.1/32")

