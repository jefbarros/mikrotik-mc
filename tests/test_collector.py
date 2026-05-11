from src.collector import collect_routeros_data, dry_run_commands
from src.commands import READ_ONLY_COMMANDS


class FakeClient:
    def __init__(self):
        self.commands = []

    def run_command(self, command):
        self.commands.append(command)
        if command == "/system package print":
            raise RuntimeError("erro secret=abc")
        return "name=test password=abc"


def test_dry_run_returns_commands_without_ssh():
    assert dry_run_commands() == READ_ONLY_COMMANDS


def test_collect_uses_allowlist_and_sanitizes(tmp_path):
    client = FakeClient()
    result = collect_routeros_data(client, tmp_path)
    assert client.commands == list(READ_ONLY_COMMANDS)
    text = result.export_path.read_text(encoding="utf-8")
    assert "password=abc" not in text
    assert "secret=abc" not in text
    assert "password=********" in text
    assert result.error_count == 1

