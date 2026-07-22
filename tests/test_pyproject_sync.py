"""Packaging-consistency tests for the .mcpb bundle sources.

These guard the invariants the build relies on: requirements.txt and the
pyproject [project].dependencies stay mirrored, the three version sources
agree, and the manifest entry point + env mapping stay wired to real files
and declared user config. A drift here silently ships a broken extension.
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _load_manifest() -> dict:
    return json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))


def _requirements_entries() -> set[str]:
    lines = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    entries = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(line)
    return entries


def _main_version() -> str:
    text = (REPO_ROOT / "personal_mcp_servicenow_main.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    assert match, "no __version__ literal found in personal_mcp_servicenow_main.py"
    return match.group(1)


@pytest.mark.unit
def test_requirements_mirrored_in_pyproject():
    req = {e for e in _requirements_entries() if not e.startswith("setuptools")}
    pyproject_deps = {d.strip() for d in _load_pyproject()["project"]["dependencies"]}
    assert req == pyproject_deps, (
        "requirements.txt (minus setuptools) and pyproject dependencies drifted:\n"
        f"  only in requirements.txt: {sorted(req - pyproject_deps)}\n"
        f"  only in pyproject:        {sorted(pyproject_deps - req)}"
    )


@pytest.mark.unit
def test_versions_aligned():
    manifest_v = _load_manifest()["version"]
    pyproject_v = _load_pyproject()["project"]["version"]
    main_v = _main_version()
    assert manifest_v == pyproject_v == main_v, (
        f"version mismatch: manifest={manifest_v}, "
        f"pyproject={pyproject_v}, __version__={main_v}"
    )


@pytest.mark.unit
def test_manifest_entry_point_exists():
    entry_point = _load_manifest()["server"]["entry_point"]
    assert (REPO_ROOT / entry_point).is_file(), (
        f"manifest entry_point {entry_point!r} does not exist at repo root"
    )


@pytest.mark.unit
def test_manifest_env_mapping_covers_required_config():
    manifest = _load_manifest()
    env = manifest["server"]["mcp_config"]["env"]

    for key in ("SERVICENOW_INSTANCE", "SERVICENOW_CLIENT_ID", "SERVICENOW_CLIENT_SECRET"):
        assert key in env, f"required env key {key} missing from manifest env mapping"

    user_config_keys = set(manifest.get("user_config", {}))
    placeholder = re.compile(r"\$\{user_config\.([^}]+)\}")
    for env_key, value in env.items():
        for referenced in placeholder.findall(str(value)):
            assert referenced in user_config_keys, (
                f"env {env_key} references ${{user_config.{referenced}}} "
                f"which is not defined in manifest user_config {sorted(user_config_keys)}"
            )
