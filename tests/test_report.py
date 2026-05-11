from datetime import datetime

from src.collector import CollectionResult, CommandResult
from src.report import generate_report


def test_report_generates_markdown_without_secrets(tmp_path):
    result = CollectionResult(
        timestamp=datetime(2026, 5, 10, 12, 0, 0),
        export_path=tmp_path / "export.txt",
        command_results=[
            CommandResult("/system identity print", "identity=router password=abc"),
            CommandResult("/ip service print detail", "0 name=ssh disabled=no address=192.168.88.0/24"),
            CommandResult("/ppp secret print detail", "name=user secret=abc"),
        ],
    )
    path = generate_report(result, "192.168.88.1", "ia-automation", tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "# Relatorio tecnico MikroTik" in text
    assert "192.168.88.1" in text
    assert "/system identity print" in text
    assert "password=abc" not in text
    assert "secret=abc" not in text

