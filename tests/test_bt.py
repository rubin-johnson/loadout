import os
import pathlib
import subprocess
import sys

import pytest
import yaml


def _make_package(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# smoke")
    (path / "manifest.yaml").write_text(
        yaml.dump(
            {
                "name": "smoke",
                "version": "0.0.1",
                "author": "ci",
                "description": "smoke test",
                "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}],
            }
        )
    )


def _cli(*args, env=None, **kwargs):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
        **kwargs,
    )


def test_bt005_smoke_validate(tmp_path):
    pkg = tmp_path / "pkg"
    _make_package(pkg)
    r = _cli("validate", str(pkg))
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_apply(tmp_path):
    pkg = tmp_path / "pkg"
    target = tmp_path / "target"
    target.mkdir()
    _make_package(pkg)
    r = _cli("apply", str(pkg), "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_status_no_state(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    r = _cli("status", "--target", str(target))
    assert r.returncode == 0
    assert "no loadout" in r.stdout.lower()


def test_bt005_smoke_restore(tmp_path):
    pkg = tmp_path / "pkg"
    target = tmp_path / "target"
    target.mkdir()
    _make_package(pkg)
    _cli("apply", str(pkg), "--target", str(target), "--yes")
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_pack(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "CLAUDE.md").write_text("# packed")
    out = tmp_path / "packed-output"
    r = _cli("pack", "--source", str(source), "--output", str(out), "--yes")
    assert r.returncode == 0, r.stderr
    assert (out / "manifest.yaml").exists()


def _run_validate(package_path):
    return subprocess.run(
        [sys.executable, "-m", "loadout", "validate", str(package_path)], capture_output=True, text=True
    )


def _make_valid_package(path: pathlib.Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# test")
    (path / "manifest.yaml").write_text(
        yaml.dump(
            {
                "name": "t",
                "version": "0.1.0",
                "author": "a",
                "description": "d",
                "targets": [{"path": "CLAUDE.md", "dest": "~/.claude/CLAUDE.md"}],
            }
        )
    )


def test_bt004_missing_manifest(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    r = _run_validate(pkg)
    assert r.returncode != 0
    assert "manifest" in r.stdout.lower() or "manifest" in r.stderr.lower()


def test_bt004_missing_required_field(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text("name: t\nversion: 0.1.0\ndescription: d\ntargets: []\n")
    r = _run_validate(pkg)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "author" in out.lower()


def test_bt004_invalid_semver(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        yaml.dump({"name": "t", "version": "not-semver", "author": "a", "description": "d", "targets": []})
    )
    r = _run_validate(pkg)
    assert r.returncode != 0


def test_bt004_missing_target_file(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        yaml.dump(
            {
                "name": "t",
                "version": "0.1.0",
                "author": "a",
                "description": "d",
                "targets": [{"path": "missing.md", "dest": "~/.claude/missing.md"}],
            }
        )
    )
    r = _run_validate(pkg)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "missing.md" in out


def test_bt004_valid_package(tmp_path):
    pkg = tmp_path / "pkg"
    _make_valid_package(pkg)
    r = _run_validate(pkg)
    assert r.returncode == 0


def test_bt003_no_tty_target(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        "name: ci-test\nversion: 0.1.0\nauthor: ci\ndescription: d\n"
        "targets:\n  - path: config.md\n    dest: config.md\n"
    )
    (pkg / "config.md").write_text("# ci config")

    target = tmp_path / "claude"
    target.mkdir()

    r = subprocess.run(
        [sys.executable, "-m", "loadout", "apply", str(pkg), "--target", str(target), "--yes"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    assert r.returncode == 0, r.stderr
    assert (target / "config.md").read_text() == "# ci config"


def test_bt003_env_var_target(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        "name: ci-test\nversion: 0.1.0\nauthor: ci\ndescription: d\n"
        "targets:\n  - path: config.md\n    dest: config.md\n"
    )
    (pkg / "config.md").write_text("# env config")

    target = tmp_path / "claude"
    target.mkdir()

    env = {**os.environ, "LOADOUT_TARGET_ROOT": str(target)}
    r = subprocess.run(
        [sys.executable, "-m", "loadout", "apply", str(pkg), "--yes"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert (target / "config.md").read_text() == "# env config"


def _dir_checksums(path: pathlib.Path) -> dict:
    result = {}
    for f in sorted(path.rglob("*")):
        if f.is_file() and ".loadout-" not in str(f):
            result[str(f.relative_to(path))] = f.read_bytes()
    return result


def test_bt001_roundtrip(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        "name: test\nversion: 0.1.0\nauthor: ci\ndescription: d\ntargets:\n  - path: CLAUDE.md\n    dest: CLAUDE.md\n"
    )
    (pkg / "CLAUDE.md").write_text("# test")

    target = tmp_path / "target"
    target.mkdir()
    (target / "CLAUDE.md").write_text("# original")
    (target / "extra.txt").write_text("keep me")

    before = _dir_checksums(target)

    r = _cli("apply", str(pkg), "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr

    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr

    after = _dir_checksums(target)
    assert before == after


def test_bt002_partial_failure_atomic(tmp_path):
    from unittest.mock import patch

    from loadout.apply import atomic_apply
    from loadout.manifest import load_manifest

    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "manifest.yaml").write_text(
        "name: test\nversion: 0.1.0\nauthor: ci\ndescription: d\ntargets:\n  - path: a.txt\n    dest: a.txt\n"
    )
    (pkg / "a.txt").write_text("new")

    target = tmp_path / "target"
    target.mkdir()
    (target / "a.txt").write_text("original")

    manifest = load_manifest(pkg)

    with patch("loadout.apply.shutil.move", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            atomic_apply(pkg, target, manifest)

    assert (target / "a.txt").read_text() == "original"
