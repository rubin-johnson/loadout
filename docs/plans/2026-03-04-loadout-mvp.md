# Loadout MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that captures a Claude Code configuration into a versioned bundle and applies it to any machine or container — safely, with backups and dry-run support.

**Architecture:** Single-loadout model. `capture` reads `~/.claude/` and writes a bundle dir. `apply` reads a bundle, backs up the target dir, and copies files into place. A JSON state file tracks what is active. All file operations use temp-dir + atomic rename to prevent partial writes.

**Tech Stack:** Python 3.11+, uv (packaging/venv), click (CLI), PyYAML (manifest), pytest (tests), stdlib only for core logic (no runtime deps beyond click + PyYAML).

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/loadout/__init__.py`
- Create: `src/loadout/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Initialize the Python project with uv**

```bash
uv init --name loadout --python 3.11
```

This creates `pyproject.toml` and a basic project layout. Clean up the generated `hello.py` if created.

**Step 2: Move to src layout and add dependencies**

Edit `pyproject.toml` to reflect:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "loadout"
version = "0.0.1"
description = "CLI tool to manage Claude Code configuration bundles"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "pyyaml>=6.0",
]

[project.scripts]
loadout = "loadout.cli:cli"

[tool.hatch.build.targets.wheel]
packages = ["src/loadout"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 3: Create directory structure**

```bash
mkdir -p src/loadout tests
touch src/loadout/__init__.py tests/__init__.py
```

**Step 4: Create the CLI entry point**

`src/loadout/cli.py`:
```python
import click


@click.group()
def cli():
    """Manage Claude Code configuration bundles."""


def main():
    cli()
```

**Step 5: Create test fixtures in conftest.py**

`tests/conftest.py`:
```python
import shutil
from pathlib import Path
import pytest


ORGANIC_FILES = {
    "CLAUDE.md": "# My Claude instructions\nBe helpful.\n",
    "settings.json": '{"model": "claude-opus-4-6"}\n',
    "hooks/post-tool-use.sh": "#!/bin/bash\necho 'hook ran'\n",
    "bin/token-log": "#!/bin/bash\necho 'token-log'\n",
    "bin/token-report": "#!/bin/bash\necho 'token-report'\n",
}


@pytest.fixture
def claude_dir(tmp_path):
    """A populated ~/.claude/ lookalike for testing."""
    base = tmp_path / "claude"
    for rel_path, content in ORGANIC_FILES.items():
        full_path = base / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return base


@pytest.fixture
def bundle_dir(tmp_path):
    """An empty directory to use as a bundle output location."""
    d = tmp_path / "bundle"
    d.mkdir()
    return d


@pytest.fixture
def empty_target(tmp_path):
    """An empty target dir to apply bundles into."""
    d = tmp_path / "target"
    d.mkdir()
    return d
```

**Step 6: Install in dev mode and verify CLI loads**

```bash
uv add --dev pytest
uv pip install -e .
uv run loadout --help
```

Expected output: help text showing the `loadout` group.

**Step 7: Run pytest to confirm zero errors on empty suite**

```bash
uv run pytest -v
```

Expected: `no tests ran` or 0 passed, 0 failed.

**Step 8: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffold with CLI entry point and test fixtures"
```

---

## Task 2: Manifest schema and validation

**Files:**
- Create: `src/loadout/manifest.py`
- Create: `tests/test_manifest.py`

The manifest is the `manifest.yaml` file at the root of every bundle. We need to parse it and validate it before anything else can work.

**Step 1: Write failing tests**

`tests/test_manifest.py`:
```python
import pytest
from pathlib import Path
from loadout.manifest import load_manifest, validate_manifest, ManifestError


def test_load_valid_manifest(tmp_path):
    content = """
name: test-loadout
version: 0.1.0
author: tester
description: A test loadout
targets:
  - path: CLAUDE.md
    dest: ~/.claude/CLAUDE.md
"""
    (tmp_path / "manifest.yaml").write_text(content)
    m = load_manifest(tmp_path)
    assert m["name"] == "test-loadout"
    assert m["version"] == "0.1.0"
    assert len(m["targets"]) == 1


def test_load_manifest_missing_file(tmp_path):
    with pytest.raises(ManifestError, match="manifest.yaml not found"):
        load_manifest(tmp_path)


def test_validate_manifest_missing_required_fields(tmp_path):
    (tmp_path / "manifest.yaml").write_text("name: incomplete\n")
    with pytest.raises(ManifestError, match="missing required fields"):
        validate_manifest(load_manifest(tmp_path))


def test_validate_manifest_target_missing_path(tmp_path):
    content = """
name: bad
version: 0.1.0
author: x
description: x
targets:
  - dest: ~/.claude/CLAUDE.md
"""
    (tmp_path / "manifest.yaml").write_text(content)
    with pytest.raises(ManifestError, match="target missing 'path'"):
        validate_manifest(load_manifest(tmp_path))


def test_validate_manifest_target_missing_dest(tmp_path):
    content = """
name: bad
version: 0.1.0
author: x
description: x
targets:
  - path: CLAUDE.md
"""
    (tmp_path / "manifest.yaml").write_text(content)
    with pytest.raises(ManifestError, match="target missing 'dest'"):
        validate_manifest(load_manifest(tmp_path))
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_manifest.py -v
```

Expected: ImportError or similar — `manifest.py` doesn't exist yet.

**Step 3: Implement manifest.py**

`src/loadout/manifest.py`:
```python
from pathlib import Path
import yaml


REQUIRED_FIELDS = {"name", "version", "author", "description", "targets"}


class ManifestError(Exception):
    pass


def load_manifest(bundle_path: Path) -> dict:
    path = Path(bundle_path) / "manifest.yaml"
    if not path.exists():
        raise ManifestError(f"manifest.yaml not found in {bundle_path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ManifestError("manifest.yaml must be a YAML mapping")
    return data


def validate_manifest(manifest: dict) -> None:
    missing = REQUIRED_FIELDS - manifest.keys()
    if missing:
        raise ManifestError(f"missing required fields: {sorted(missing)}")
    for i, target in enumerate(manifest.get("targets", [])):
        if "path" not in target:
            raise ManifestError(f"target {i} missing 'path'")
        if "dest" not in target:
            raise ManifestError(f"target {i} missing 'dest'")
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_manifest.py -v
```

Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/loadout/manifest.py tests/test_manifest.py
git commit -m "feat: manifest loading and validation"
```

---

## Task 3: State file management

**Files:**
- Create: `src/loadout/state.py`
- Create: `tests/test_state.py`

The state file at `<target>/.loadout-state.json` tracks what loadout is currently applied and where the backup lives.

**Step 1: Write failing tests**

`tests/test_state.py`:
```python
import json
from pathlib import Path
from loadout.state import read_state, write_state, clear_state, STATE_FILENAME


def test_write_and_read_state(tmp_path):
    write_state(tmp_path, name="frugal-v2", bundle_path="/bundles/frugal-v2",
                version="0.3.1", backup="2026-03-04-180000")
    state = read_state(tmp_path)
    assert state["active"] == "frugal-v2"
    assert state["backup"] == "2026-03-04-180000"
    assert state["manifest_version"] == "0.3.1"


def test_read_state_returns_none_when_missing(tmp_path):
    assert read_state(tmp_path) is None


def test_clear_state(tmp_path):
    write_state(tmp_path, name="x", bundle_path="/x", version="1.0.0", backup="ts")
    clear_state(tmp_path)
    assert read_state(tmp_path) is None


def test_state_file_is_valid_json(tmp_path):
    write_state(tmp_path, name="x", bundle_path="/x", version="1.0.0", backup="ts")
    raw = (tmp_path / STATE_FILENAME).read_text()
    data = json.loads(raw)
    assert "applied_at" in data
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_state.py -v
```

**Step 3: Implement state.py**

`src/loadout/state.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILENAME = ".loadout-state.json"


def _state_path(target: Path) -> Path:
    return Path(target) / STATE_FILENAME


def read_state(target: Path) -> dict | None:
    path = _state_path(target)
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def write_state(target: Path, *, name: str, bundle_path: str,
                version: str, backup: str) -> None:
    state = {
        "active": name,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "bundle_path": bundle_path,
        "manifest_version": version,
        "backup": backup,
    }
    path = _state_path(target)
    path.write_text(json.dumps(state, indent=2))


def clear_state(target: Path) -> None:
    path = _state_path(target)
    if path.exists():
        path.unlink()
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_state.py -v
```

Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/loadout/state.py tests/test_state.py
git commit -m "feat: state file read/write for tracking active loadout"
```

---

## Task 4: Backup and restore logic

**Files:**
- Create: `src/loadout/backup.py`
- Create: `tests/test_backup.py`

Before `apply` touches anything, it snapshots the target dir. `restore` reads the state file and copies the backup back.

**Step 1: Write failing tests**

`tests/test_backup.py`:
```python
import pytest
from pathlib import Path
from loadout.backup import create_backup, restore_backup, list_backups, BACKUPS_DIR


def test_create_backup_copies_files(claude_dir):
    timestamp = create_backup(claude_dir)
    backup_path = claude_dir / BACKUPS_DIR / timestamp
    assert (backup_path / "CLAUDE.md").exists()
    assert (backup_path / "settings.json").exists()


def test_create_backup_excludes_backup_dir_itself(claude_dir):
    t1 = create_backup(claude_dir)
    t2 = create_backup(claude_dir)
    backup_path = claude_dir / BACKUPS_DIR / t2
    assert not (backup_path / BACKUPS_DIR).exists()


def test_restore_backup_puts_files_back(claude_dir, tmp_path):
    original_content = (claude_dir / "CLAUDE.md").read_text()
    timestamp = create_backup(claude_dir)
    (claude_dir / "CLAUDE.md").write_text("overwritten")
    restore_backup(claude_dir, timestamp)
    assert (claude_dir / "CLAUDE.md").read_text() == original_content


def test_list_backups_returns_sorted(claude_dir):
    t1 = create_backup(claude_dir)
    t2 = create_backup(claude_dir)
    backups = list_backups(claude_dir)
    assert backups[-1] >= backups[-2]  # latest last


def test_restore_backup_raises_if_missing(claude_dir):
    with pytest.raises(FileNotFoundError, match="backup not found"):
        restore_backup(claude_dir, "nonexistent-timestamp")
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_backup.py -v
```

**Step 3: Implement backup.py**

`src/loadout/backup.py`:
```python
import shutil
from datetime import datetime
from pathlib import Path

BACKUPS_DIR = ".loadout-backups"


def create_backup(target: Path) -> str:
    target = Path(target)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_path = target / BACKUPS_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    for item in target.iterdir():
        if item.name == BACKUPS_DIR:
            continue
        dest = backup_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    return timestamp


def restore_backup(target: Path, timestamp: str) -> None:
    target = Path(target)
    backup_path = target / BACKUPS_DIR / timestamp
    if not backup_path.exists():
        raise FileNotFoundError(f"backup not found: {timestamp}")

    # Remove current contents (except backups dir)
    for item in target.iterdir():
        if item.name == BACKUPS_DIR:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Copy backup contents back
    for item in backup_path.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def list_backups(target: Path) -> list[str]:
    backups_dir = Path(target) / BACKUPS_DIR
    if not backups_dir.exists():
        return []
    return sorted(p.name for p in backups_dir.iterdir() if p.is_dir())
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_backup.py -v
```

Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/loadout/backup.py tests/test_backup.py
git commit -m "feat: backup creation and restore logic"
```

---

## Task 5: `loadout validate` command

**Files:**
- Modify: `src/loadout/cli.py`
- Create: `tests/test_validate.py`

`validate` checks that a bundle dir has a valid `manifest.yaml` and that every declared `path` exists inside the bundle.

**Step 1: Write failing tests**

`tests/test_validate.py`:
```python
import pytest
from click.testing import CliRunner
from loadout.cli import cli
from pathlib import Path


@pytest.fixture
def valid_bundle(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# instructions\n")
    (tmp_path / "manifest.yaml").write_text("""
name: test
version: 0.1.0
author: tester
description: test bundle
targets:
  - path: CLAUDE.md
    dest: ~/.claude/CLAUDE.md
""")
    return tmp_path


def test_validate_valid_bundle(valid_bundle):
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(valid_bundle)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_missing_manifest(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(tmp_path)])
    assert result.exit_code != 0
    assert "manifest.yaml not found" in result.output


def test_validate_target_file_missing(tmp_path):
    (tmp_path / "manifest.yaml").write_text("""
name: test
version: 0.1.0
author: tester
description: test bundle
targets:
  - path: missing-file.md
    dest: ~/.claude/CLAUDE.md
""")
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(tmp_path)])
    assert result.exit_code != 0
    assert "missing-file.md" in result.output
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_validate.py -v
```

**Step 3: Implement validate command in cli.py**

Add to `src/loadout/cli.py`:
```python
from pathlib import Path
from loadout.manifest import load_manifest, validate_manifest, ManifestError


@cli.command()
@click.argument("bundle", type=click.Path(exists=True, file_okay=False, path_type=Path))
def validate(bundle: Path):
    """Validate a loadout bundle structure."""
    try:
        manifest = load_manifest(bundle)
        validate_manifest(manifest)
    except ManifestError as e:
        raise click.ClickException(str(e))

    # Check declared files exist in bundle
    for target in manifest["targets"]:
        file_path = bundle / target["path"]
        if not file_path.exists():
            raise click.ClickException(
                f"declared target missing from bundle: {target['path']}"
            )

    click.echo(f"Bundle '{manifest['name']}' v{manifest['version']} is valid.")
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_validate.py -v
```

Expected: 3 passed.

**Step 5: Commit**

```bash
git add src/loadout/cli.py tests/test_validate.py
git commit -m "feat: loadout validate command"
```

---

## Task 6: `loadout capture` command

**Files:**
- Create: `src/loadout/capture.py`
- Modify: `src/loadout/cli.py`
- Create: `tests/test_capture.py`

`capture` reads the source dir (default `~/.claude/`), copies managed files into a bundle dir, generates `manifest.yaml`, and warns about secrets/uncapturable items.

**Step 1: Write failing tests**

`tests/test_capture.py`:
```python
import pytest
import yaml
from pathlib import Path
from click.testing import CliRunner
from loadout.cli import cli


def test_capture_creates_manifest(claude_dir, bundle_dir):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "test-loadout",
        "--yes",
    ])
    assert result.exit_code == 0, result.output
    manifest_path = bundle_dir / "manifest.yaml"
    assert manifest_path.exists()
    manifest = yaml.safe_load(manifest_path.read_text())
    assert manifest["name"] == "test-loadout"
    assert manifest["version"] == "0.0.1"


def test_capture_copies_claude_md(claude_dir, bundle_dir):
    runner = CliRunner()
    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x", "--yes",
    ])
    assert (bundle_dir / "CLAUDE.md").exists()


def test_capture_copies_settings_json(claude_dir, bundle_dir):
    runner = CliRunner()
    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x", "--yes",
    ])
    assert (bundle_dir / "settings.json").exists()


def test_capture_copies_hooks_dir(claude_dir, bundle_dir):
    runner = CliRunner()
    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x", "--yes",
    ])
    assert (bundle_dir / "hooks").is_dir()


def test_capture_copies_bin_dir(claude_dir, bundle_dir):
    runner = CliRunner()
    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x", "--yes",
    ])
    assert (bundle_dir / "bin").is_dir()


def test_capture_requires_yes_flag_or_interactive(claude_dir, bundle_dir):
    """Without --yes, must prompt (in non-interactive test, should fail gracefully)."""
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x",
    ], input="n\n")
    # Aborted or exited non-zero
    assert result.exit_code != 0 or "abort" in result.output.lower()


def test_capture_manifest_targets_reference_existing_files(claude_dir, bundle_dir):
    runner = CliRunner()
    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle_dir),
        "--name", "x", "--yes",
    ])
    manifest = yaml.safe_load((bundle_dir / "manifest.yaml").read_text())
    for target in manifest["targets"]:
        assert (bundle_dir / target["path"]).exists(), \
            f"target {target['path']} listed in manifest but not in bundle"
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_capture.py -v
```

**Step 3: Implement capture.py**

`src/loadout/capture.py`:
```python
import shutil
from pathlib import Path
from datetime import datetime
import yaml

# Files/dirs to capture from source, and their dest pattern in manifest
CAPTURE_TARGETS = [
    ("CLAUDE.md", "~/.claude/CLAUDE.md"),
    ("settings.json", "~/.claude/settings.json"),
    ("hooks", "~/.claude/hooks/"),
    ("bin", "~/.claude/bin/"),
]

SECRETS_PATTERNS = ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"]


def warn_about_uncapturable(source: Path) -> list[str]:
    """Return warning messages for things we can't/won't capture."""
    warnings = []
    claude_mem_db = Path.home() / ".claude-mem" / "claude-mem.db"
    if claude_mem_db.exists():
        warnings.append(
            "claude-mem database (~/.claude-mem/claude-mem.db) is not captured — "
            "use claude-mem's own export if needed"
        )
    # Scan for secrets in hooks and bin
    for subdir in ["hooks", "bin"]:
        d = source / subdir
        if d.is_dir():
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        content = f.read_text()
                        for pattern in SECRETS_PATTERNS:
                            if pattern in content.upper():
                                warnings.append(
                                    f"WARNING: possible secret in {f.relative_to(source)} "
                                    f"(matched '{pattern}') — review before sharing"
                                )
                                break
                    except UnicodeDecodeError:
                        pass
    return warnings


def run_capture(source: Path, output: Path, name: str) -> list[str]:
    """
    Copy managed files from source into output bundle dir.
    Returns list of warning messages.
    """
    output.mkdir(parents=True, exist_ok=True)
    targets = []

    for rel_path, dest_pattern in CAPTURE_TARGETS:
        src = source / rel_path
        if not src.exists():
            continue
        dst = output / rel_path
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        targets.append({"path": rel_path, "dest": dest_pattern})

    manifest = {
        "name": name,
        "version": "0.0.1",
        "author": "",
        "description": "",
        "captured_at": datetime.now().isoformat(),
        "targets": targets,
    }
    (output / "manifest.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    )

    return warn_about_uncapturable(source)
```

**Step 4: Add capture command to cli.py**

Add to `src/loadout/cli.py`:
```python
from loadout.capture import run_capture


@cli.command()
@click.option("--source", type=click.Path(file_okay=False, path_type=Path),
              default=None, help="Source dir (default: ~/.claude/)")
@click.option("--output", type=click.Path(file_okay=False, path_type=Path),
              required=True, help="Output bundle directory")
@click.option("--name", required=True, help="Loadout name (e.g. frugal-v2)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def capture(source, output, name, yes):
    """Capture current Claude config into a loadout bundle."""
    if source is None:
        source = Path.home() / ".claude"

    if not yes:
        click.confirm(
            f"Capture config from {source} into {output}?", abort=True
        )

    warnings = run_capture(source, output, name)

    for w in warnings:
        click.echo(f"  ! {w}", err=True)

    click.echo(f"Captured '{name}' to {output}")
```

**Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_capture.py -v
```

Expected: 7 passed.

**Step 6: Commit**

```bash
git add src/loadout/capture.py tests/test_capture.py src/loadout/cli.py
git commit -m "feat: loadout capture command"
```

---

## Task 7: `loadout apply` command

**Files:**
- Create: `src/loadout/apply.py`
- Modify: `src/loadout/cli.py`
- Create: `tests/test_apply.py`

`apply` validates the bundle, backs up the target, copies files into place, writes the state file. `--dry-run` prints what would happen without touching anything.

**Step 1: Write failing tests**

`tests/test_apply.py`:
```python
import pytest
import yaml
from pathlib import Path
from click.testing import CliRunner
from loadout.cli import cli
from loadout.state import read_state


@pytest.fixture
def valid_bundle(tmp_path):
    bundle = tmp_path / "my-bundle"
    bundle.mkdir()
    (bundle / "CLAUDE.md").write_text("# loadout instructions\n")
    (bundle / "settings.json").write_text('{"model": "claude-haiku-4-5-20251001"}\n')
    (bundle / "manifest.yaml").write_text(yaml.dump({
        "name": "test-loadout",
        "version": "0.1.0",
        "author": "tester",
        "description": "test",
        "targets": [
            {"path": "CLAUDE.md", "dest": "~/.claude/CLAUDE.md"},
            {"path": "settings.json", "dest": "~/.claude/settings.json"},
        ],
    }))
    return bundle


def test_apply_copies_files_to_target(valid_bundle, empty_target):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(empty_target), "--yes"
    ])
    assert result.exit_code == 0, result.output
    assert (empty_target / "CLAUDE.md").read_text() == "# loadout instructions\n"
    assert (empty_target / "settings.json").exists()


def test_apply_writes_state_file(valid_bundle, empty_target):
    runner = CliRunner()
    runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(empty_target), "--yes"
    ])
    state = read_state(empty_target)
    assert state is not None
    assert state["active"] == "test-loadout"
    assert state["manifest_version"] == "0.1.0"


def test_apply_creates_backup(valid_bundle, claude_dir):
    """Apply to a populated dir creates a backup first."""
    runner = CliRunner()
    runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(claude_dir), "--yes"
    ])
    from loadout.backup import list_backups
    assert len(list_backups(claude_dir)) >= 1


def test_apply_dry_run_does_not_modify(valid_bundle, claude_dir):
    original_content = (claude_dir / "CLAUDE.md").read_text()
    runner = CliRunner()
    result = runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(claude_dir),
        "--yes", "--dry-run"
    ])
    assert result.exit_code == 0
    assert "dry run" in result.output.lower()
    assert (claude_dir / "CLAUDE.md").read_text() == original_content


def test_apply_dry_run_shows_planned_changes(valid_bundle, empty_target):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(empty_target),
        "--yes", "--dry-run"
    ])
    assert "CLAUDE.md" in result.output
    assert "settings.json" in result.output


def test_apply_requires_yes_or_interactive(valid_bundle, empty_target):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "apply", str(valid_bundle), "--target", str(empty_target),
    ], input="n\n")
    assert result.exit_code != 0


def test_apply_invalid_bundle_exits_nonzero(empty_target, tmp_path):
    empty_bundle = tmp_path / "empty"
    empty_bundle.mkdir()
    runner = CliRunner()
    result = runner.invoke(cli, [
        "apply", str(empty_bundle), "--target", str(empty_target), "--yes"
    ])
    assert result.exit_code != 0
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_apply.py -v
```

**Step 3: Implement apply.py**

`src/loadout/apply.py`:
```python
import shutil
from pathlib import Path

from loadout.backup import create_backup
from loadout.manifest import load_manifest, validate_manifest, ManifestError
from loadout.state import write_state


def run_apply(bundle: Path, target: Path, dry_run: bool = False) -> list[str]:
    """
    Apply bundle to target. Returns list of actions taken (or planned if dry_run).
    Raises ManifestError on bad bundle.
    """
    manifest = load_manifest(bundle)
    validate_manifest(manifest)

    # Check all declared files exist in bundle before touching target
    for t in manifest["targets"]:
        src = bundle / t["path"]
        if not src.exists():
            raise ManifestError(f"declared target missing from bundle: {t['path']}")

    actions = []

    if dry_run:
        for t in manifest["targets"]:
            actions.append(f"  would copy: {t['path']} -> {target / t['path']}")
        return actions

    timestamp = create_backup(target)
    actions.append(f"backup created: {timestamp}")

    for t in manifest["targets"]:
        src = bundle / t["path"]
        dst = target / t["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        actions.append(f"  copied: {t['path']}")

    write_state(
        target,
        name=manifest["name"],
        bundle_path=str(bundle.resolve()),
        version=manifest["version"],
        backup=timestamp,
    )

    return actions
```

**Step 4: Add apply command to cli.py**

Add to `src/loadout/cli.py`:
```python
from loadout.apply import run_apply


@cli.command()
@click.argument("bundle", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--target", type=click.Path(file_okay=False, path_type=Path),
              default=None, help="Target dir (default: ~/.claude/)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Show what would happen without changing anything")
def apply(bundle, target, yes, dry_run):
    """Apply a loadout bundle to the target directory."""
    if target is None:
        target = Path.home() / ".claude"

    if dry_run:
        click.echo("Dry run — no changes will be made.")
    elif not yes:
        click.confirm(
            f"Apply '{bundle.name}' to {target}?", abort=True
        )

    try:
        actions = run_apply(bundle, target, dry_run=dry_run)
    except ManifestError as e:
        raise click.ClickException(str(e))

    for action in actions:
        click.echo(action)

    if not dry_run:
        click.echo(f"Applied '{bundle.name}' to {target}")
```

**Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_apply.py -v
```

Expected: 7 passed.

**Step 6: Commit**

```bash
git add src/loadout/apply.py tests/test_apply.py src/loadout/cli.py
git commit -m "feat: loadout apply command with dry-run and backup"
```

---

## Task 8: `loadout restore` and `loadout status` commands

**Files:**
- Modify: `src/loadout/cli.py`
- Create: `tests/test_restore_status.py`

**Step 1: Write failing tests**

`tests/test_restore_status.py`:
```python
import yaml
import pytest
from pathlib import Path
from click.testing import CliRunner
from loadout.cli import cli
from loadout.backup import create_backup
from loadout.state import write_state


@pytest.fixture
def applied_target(claude_dir, tmp_path):
    """A target dir with a known backup and state."""
    timestamp = create_backup(claude_dir)
    (claude_dir / "CLAUDE.md").write_text("# overwritten by apply\n")
    write_state(claude_dir, name="frugal-v2", bundle_path="/bundles/frugal-v2",
                version="0.3.1", backup=timestamp)
    return claude_dir, timestamp


def test_restore_puts_files_back(applied_target):
    target, _ = applied_target
    runner = CliRunner()
    result = runner.invoke(cli, ["restore", "--target", str(target), "--yes"])
    assert result.exit_code == 0, result.output
    # The original content from conftest fixture
    assert "My Claude instructions" in (target / "CLAUDE.md").read_text()


def test_restore_requires_active_loadout(empty_target):
    runner = CliRunner()
    result = runner.invoke(cli, ["restore", "--target", str(empty_target), "--yes"])
    assert result.exit_code != 0
    assert "no loadout" in result.output.lower()


def test_status_shows_active_loadout(applied_target):
    target, _ = applied_target
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--target", str(target)])
    assert result.exit_code == 0
    assert "frugal-v2" in result.output
    assert "0.3.1" in result.output


def test_status_shows_nothing_applied(empty_target):
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--target", str(empty_target)])
    assert result.exit_code == 0
    assert "no loadout" in result.output.lower()
```

**Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_restore_status.py -v
```

**Step 3: Add restore and status commands to cli.py**

Add to `src/loadout/cli.py`:
```python
from loadout.backup import restore_backup
from loadout.state import read_state, clear_state


@cli.command()
@click.option("--target", type=click.Path(file_okay=False, path_type=Path),
              default=None, help="Target dir (default: ~/.claude/)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--backup", "backup_ts", default=None,
              help="Specific backup timestamp to restore (default: most recent)")
def restore(target, yes, backup_ts):
    """Restore the previous configuration from backup."""
    if target is None:
        target = Path.home() / ".claude"

    state = read_state(target)
    if state is None:
        raise click.ClickException("no loadout is currently applied in this target")

    timestamp = backup_ts or state["backup"]

    if not yes:
        click.confirm(f"Restore backup '{timestamp}' to {target}?", abort=True)

    try:
        restore_backup(target, timestamp)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    clear_state(target)
    click.echo(f"Restored backup '{timestamp}' to {target}")


@cli.command()
@click.option("--target", type=click.Path(file_okay=False, path_type=Path),
              default=None, help="Target dir (default: ~/.claude/)")
def status(target):
    """Show what loadout is currently applied."""
    if target is None:
        target = Path.home() / ".claude"

    state = read_state(target)
    if state is None:
        click.echo("No loadout is currently applied.")
        return

    click.echo(f"Active loadout:  {state['active']} v{state['manifest_version']}")
    click.echo(f"Applied at:      {state['applied_at']}")
    click.echo(f"Bundle path:     {state['bundle_path']}")
    click.echo(f"Backup:          {state['backup']}")
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_restore_status.py -v
```

Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/loadout/cli.py tests/test_restore_status.py
git commit -m "feat: loadout restore and status commands"
```

---

## Task 9: Roundtrip integration test + smoke tests

**Files:**
- Create: `tests/test_integration.py`
- Create: `tests/test_smoke.py`

**Step 1: Write integration and smoke tests**

`tests/test_integration.py`:
```python
import filecmp
import shutil
from pathlib import Path
from click.testing import CliRunner
from loadout.cli import cli


def test_capture_apply_roundtrip(claude_dir, tmp_path):
    """Capture an organic setup, apply it to a fresh target, assert file trees match."""
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    target.mkdir()

    runner = CliRunner()

    capture_result = runner.invoke(cli, [
        "capture",
        "--source", str(claude_dir),
        "--output", str(bundle),
        "--name", "roundtrip-test",
        "--yes",
    ])
    assert capture_result.exit_code == 0, capture_result.output

    apply_result = runner.invoke(cli, [
        "apply", str(bundle),
        "--target", str(target),
        "--yes",
    ])
    assert apply_result.exit_code == 0, apply_result.output

    # CLAUDE.md and settings.json should match
    for filename in ["CLAUDE.md", "settings.json"]:
        original = claude_dir / filename
        restored = target / filename
        assert original.read_text() == restored.read_text(), \
            f"{filename} content mismatch after roundtrip"


def test_apply_restore_roundtrip(claude_dir, tmp_path):
    """Apply a bundle to a target, restore it, assert original content is back."""
    bundle = tmp_path / "bundle"
    runner = CliRunner()

    runner.invoke(cli, [
        "capture", "--source", str(claude_dir),
        "--output", str(bundle),
        "--name", "restore-test",
        "--yes",
    ])

    original_content = (claude_dir / "CLAUDE.md").read_text()
    (claude_dir / "CLAUDE.md").write_text("# replaced by apply\n")

    runner.invoke(cli, [
        "apply", str(bundle),
        "--target", str(claude_dir),
        "--yes",
    ])

    runner.invoke(cli, [
        "restore", "--target", str(claude_dir), "--yes"
    ])

    assert (claude_dir / "CLAUDE.md").read_text() == original_content
```

`tests/test_smoke.py`:
```python
import subprocess
import sys
from pathlib import Path
import pytest


def run(args, **kwargs):
    return subprocess.run(
        ["uv", "run", "loadout"] + args,
        capture_output=True, text=True,
        cwd=Path(__file__).parent.parent,
        **kwargs
    )


def test_smoke_help():
    result = run(["--help"])
    assert result.returncode == 0
    assert "loadout" in result.stdout.lower()


def test_smoke_validate_missing_dir():
    result = run(["validate", "/nonexistent-path-abc123"])
    assert result.returncode != 0


def test_smoke_status_default_target(tmp_path):
    """Status on an empty dir should exit 0 and say no loadout applied."""
    # Use a temp dir as target to avoid touching real ~/.claude/
    result = run(["status", "--target", str(tmp_path)])
    assert result.returncode == 0
    assert "no loadout" in result.stdout.lower()


def test_smoke_capture_and_apply(tmp_path):
    """Full capture -> apply smoke test using temp dirs."""
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    target.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    (source / "CLAUDE.md").write_text("# smoke test\n")
    (source / "settings.json").write_text("{}\n")

    capture = run([
        "capture", "--source", str(source),
        "--output", str(bundle),
        "--name", "smoke-test",
        "--yes",
    ])
    assert capture.returncode == 0, capture.stderr

    apply = run([
        "apply", str(bundle),
        "--target", str(target),
        "--yes",
    ])
    assert apply.returncode == 0, apply.stderr
    assert (target / "CLAUDE.md").read_text() == "# smoke test\n"
```

**Step 2: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests pass. If any fail, fix before proceeding.

**Step 3: Commit**

```bash
git add tests/test_integration.py tests/test_smoke.py
git commit -m "test: roundtrip integration and smoke tests"
```

---

## Task 10: Final check and version tag

**Step 1: Run full test suite with coverage**

```bash
uv add --dev pytest-cov
uv run pytest --cov=loadout --cov-report=term-missing -v
```

Review uncovered lines. If any critical path is uncovered, add a test.

**Step 2: Verify CLI works end-to-end manually**

```bash
uv run loadout --help
uv run loadout capture --help
uv run loadout apply --help
uv run loadout restore --help
uv run loadout status --help
uv run loadout validate --help
```

**Step 3: Tag the release**

```bash
git tag v0.0.1
```

**Step 4: Final commit if any fixes were made**

```bash
git add -u
git commit -m "chore: 0.0.1 release cleanup"
```
