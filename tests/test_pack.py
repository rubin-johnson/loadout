import subprocess
import sys

import yaml

from loadout.validate import validate_package


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL
    )


def _make_source(tmp_path):
    src = tmp_path / "claude"
    src.mkdir()
    (src / "CLAUDE.md").write_text("# global")
    (src / "settings.json").write_text('{"model": "sonnet"}')
    hooks = src / "hooks"
    hooks.mkdir()
    (hooks / "pre.sh").write_text("#!/bin/bash\necho hi")
    return src


def test_pack_produces_valid_package(tmp_path):
    src = _make_source(tmp_path)
    out = tmp_path / "out"
    r = _cli("pack", "--source", str(src), "--output", str(out), "--yes")
    assert r.returncode == 0, r.stderr
    errors = validate_package(out)
    assert errors == [], errors


def test_pack_targets_include_all_files(tmp_path):
    src = _make_source(tmp_path)
    out = tmp_path / "out"
    _cli("pack", "--source", str(src), "--output", str(out), "--yes")
    manifest = yaml.safe_load((out / "manifest.yaml").read_text())
    dest_paths = {t["dest"] for t in manifest["targets"]}
    assert "CLAUDE.md" in dest_paths
    assert "settings.json" in dest_paths


def test_pack_warns_about_secrets(tmp_path):
    src = tmp_path / "claude"
    src.mkdir()
    (src / "CLAUDE.md").write_text("# ok")
    bin_dir = src / "bin"
    bin_dir.mkdir()
    (bin_dir / "my-script.sh").write_text("export TOKEN=supersecret\n")
    out = tmp_path / "out"
    r = _cli("pack", "--source", str(src), "--output", str(out), "--yes")
    assert r.returncode == 0
    assert "secret" in r.stderr.lower() or "TOKEN" in r.stderr


def test_pack_warns_about_db(tmp_path):
    src = tmp_path / "claude"
    src.mkdir()
    (src / "CLAUDE.md").write_text("# ok")
    (src / "claude-mem.db").write_bytes(b"SQLite")
    out = tmp_path / "out"
    r = _cli("pack", "--source", str(src), "--output", str(out), "--yes")
    assert "db" in r.stderr.lower() or "database" in r.stderr.lower() or "claude-mem" in r.stderr


def test_pack_missing_optional_dirs(tmp_path):
    src = tmp_path / "claude"
    src.mkdir()
    (src / "CLAUDE.md").write_text("# minimal")
    out = tmp_path / "out"
    r = _cli("pack", "--source", str(src), "--output", str(out), "--yes")
    assert r.returncode == 0


def test_pack_default_output_name(tmp_path, monkeypatch):
    src = tmp_path / "claude"
    src.mkdir()
    (src / "CLAUDE.md").write_text("# x")
    monkeypatch.chdir(tmp_path)
    _cli("pack", "--source", str(src), "--yes")
    assert (tmp_path / "my-loadout" / "manifest.yaml").exists()


def test_pack_includes_agents_md(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "AGENTS.md").write_text("# agent instructions")
    output = tmp_path / "output"
    from loadout.pack import pack

    pack(source, output, yes=True)
    assert (output / "AGENTS.md").exists()
    manifest = yaml.safe_load((output / "manifest.yaml").read_text())
    targets = [t["path"] for t in manifest["targets"]]
    assert "AGENTS.md" in targets


def test_capture_alias_works(tmp_path):
    src = _make_source(tmp_path)
    out = tmp_path / "out"
    r = _cli("capture", "--source", str(src), "--output", str(out), "--yes")
    assert r.returncode == 0, r.stderr
    errors = validate_package(out)
    assert errors == [], errors
