from src.diff import generate_diff_report


def test_diff_generates_report_without_secrets(tmp_path):
    before = tmp_path / "before.txt"
    after = tmp_path / "after.txt"
    before.write_text("=== COMMAND: /system identity print ===\nname=a secret=old\n", encoding="utf-8")
    after.write_text("=== COMMAND: /system identity print ===\nname=b secret=new\n", encoding="utf-8")
    result = generate_diff_report(before, after, tmp_path)
    text = result.report_path.read_text(encoding="utf-8")
    assert result.changed_sections == 1
    assert "secret=old" not in text
    assert "secret=new" not in text
    assert "secret=********" in text

