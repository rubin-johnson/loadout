import subprocess
import sys
import pathlib
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
