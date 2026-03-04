import pathlib
from loadout.secrets import scan_for_secrets


def _file(tmp_path, content):
    f = tmp_path / "script.sh"
    f.write_text(content)
    return f


def test_clean_file(tmp_path):
    f = _file(tmp_path, "#!/bin/bash\necho hello\n")
    assert scan_for_secrets(f) == []


def test_detects_akia(tmp_path):
    f = _file(tmp_path, "export AWS_KEY=AKIAIOSFODNN7EXAMPLE\n")
    warnings = scan_for_secrets(f)
    assert len(warnings) == 1
    assert "1" in warnings[0]  # line number


def test_detects_ghp_prefix(tmp_path):
    f = _file(tmp_path, "TOKEN=ghp_abc123def456\n")
    assert len(scan_for_secrets(f)) == 1


def test_detects_sk_prefix(tmp_path):
    f = _file(tmp_path, "OPENAI_KEY=sk-abc123\n")
    assert len(scan_for_secrets(f)) == 1


def test_detects_export_token(tmp_path):
    f = _file(tmp_path, "export TOKEN=mysecret\n")
    assert len(scan_for_secrets(f)) == 1


def test_ignores_empty_export(tmp_path):
    f = _file(tmp_path, "export TOKEN=\n")
    assert scan_for_secrets(f) == []


def test_multiple_secrets(tmp_path):
    content = "export TOKEN=abc\nexport SECRET=xyz\n"
    f = _file(tmp_path, content)
    assert len(scan_for_secrets(f)) == 2
