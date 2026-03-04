import subprocess
import sys
import pathlib
import pytest
import yaml


def _make_bundle(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# smoke")
    (path / "manifest.yaml").write_text(yaml.dump({
        "name": "smoke", "version": "0.0.1", "author": "ci",
        "description": "smoke test",
        "targets": [{"path": "CLAUDE.md", "dest": "CLAUDE.md"}]
    }))


def _cli(*args, env=None, **kwargs):
    return subprocess.run(
        [sys.executable, "-m", "loadout", *args],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
        env=env, **kwargs
    )


def test_bt005_smoke_validate(tmp_path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    r = _cli("validate", str(bundle))
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_apply(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    target.mkdir()
    _make_bundle(bundle)
    r = _cli("apply", str(bundle), "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_status_no_state(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    r = _cli("status", "--target", str(target))
    assert r.returncode == 0
    assert "no loadout" in r.stdout.lower()


def test_bt005_smoke_restore(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    target.mkdir()
    _make_bundle(bundle)
    _cli("apply", str(bundle), "--target", str(target), "--yes")
    r = _cli("restore", "--target", str(target), "--yes")
    assert r.returncode == 0, r.stderr


def test_bt005_smoke_capture(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "CLAUDE.md").write_text("# captured")
    out = tmp_path / "captured-bundle"
    r = _cli("capture", "--source", str(source), "--output", str(out), "--yes")
    assert r.returncode == 0, r.stderr
    assert (out / "manifest.yaml").exists()


def _run_validate(bundle_path):
    return subprocess.run(
        [sys.executable, "-m", "loadout", "validate", str(bundle_path)],
        capture_output=True, text=True
    )


def _make_valid_bundle(path: pathlib.Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text("# test")
    (path / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "0.1.0", "author": "a",
        "description": "d",
        "targets": [{"path": "CLAUDE.md", "dest": "~/.claude/CLAUDE.md"}]
    }))


def test_bt004_missing_manifest(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    r = _run_validate(bundle)
    assert r.returncode != 0
    assert "manifest" in r.stdout.lower() or "manifest" in r.stderr.lower()


def test_bt004_missing_required_field(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.yaml").write_text(
        "name: t\nversion: 0.1.0\ndescription: d\ntargets: []\n"
    )
    r = _run_validate(bundle)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "author" in out.lower()


def test_bt004_invalid_semver(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "not-semver", "author": "a",
        "description": "d", "targets": []
    }))
    r = _run_validate(bundle)
    assert r.returncode != 0


def test_bt004_missing_target_file(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.yaml").write_text(yaml.dump({
        "name": "t", "version": "0.1.0", "author": "a",
        "description": "d",
        "targets": [{"path": "missing.md", "dest": "~/.claude/missing.md"}]
    }))
    r = _run_validate(bundle)
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "missing.md" in out


def test_bt004_valid_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    _make_valid_bundle(bundle)
    r = _run_validate(bundle)
    assert r.returncode == 0


def test_bt002_partial_failure_atomic(tmp_path):
    from loadout.apply import atomic_apply
    from loadout.manifest import load_manifest
    from unittest.mock import patch

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.yaml").write_text(
        "name: test\nversion: 0.1.0\nauthor: ci\ndescription: d\n"
        "targets:\n  - path: a.txt\n    dest: a.txt\n"
    )
    (bundle / "a.txt").write_text("new")

    target = tmp_path / "target"
    target.mkdir()
    (target / "a.txt").write_text("original")

    manifest = load_manifest(bundle)

    with patch("loadout.apply.shutil.move", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            atomic_apply(bundle, target, manifest)

    assert (target / "a.txt").read_text() == "original"
