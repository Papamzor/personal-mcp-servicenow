"""Build the Claude Desktop Extension (.mcpb) bundle.

A .mcpb is a zip of ``manifest.json`` + server code, produced by the
``mcpb`` CLI (npm: ``@anthropic-ai/mcpb``). This script never packs from
the repo root directly — a live ``.env`` with real secrets lives there.
Instead it copies an explicit whitelist into ``dist/mcpb-staging/`` and
packs from there, asserting no secret/junk files leaked in.

Run:
    python scripts/build_mcpb.py

Output:
    dist/personal-mcp-servicenow-<version>.mcpb
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING = REPO_ROOT / "dist" / "mcpb-staging"

# Root files copied verbatim (all required unless noted).
ROOT_FILES = [
    "personal_mcp_servicenow_main.py",
    "tools.py",
    "constants.py",
    "config_loader.py",
    "utils.py",
    "utility_tools.py",
    "audit_middleware.py",
    "auth_middleware.py",
    "param_coercion.py",
    "table_spec.py",
    "tool_registry.py",
    "manifest.json",
    "pyproject.toml",
    "LICENSE",
]
OPTIONAL_ROOT_FILES = ["icon.png"]

# Package dirs — .py files only, skip __pycache__.
PACKAGE_DIRS = ["Table_Tools", "filter", "http_layer", "oauth"]


def fail(message: str) -> None:
    """Print an error and exit nonzero."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def clean_staging() -> None:
    """Remove any prior staging dir and recreate it empty."""
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)


def copy_root_files() -> int:
    """Copy whitelisted root files into staging. Returns count copied."""
    copied = 0
    for name in ROOT_FILES:
        src = REPO_ROOT / name
        if not src.is_file():
            fail(f"required root file missing: {name}")
        shutil.copy2(src, STAGING / name)
        copied += 1
    for name in OPTIONAL_ROOT_FILES:
        src = REPO_ROOT / name
        if src.is_file():
            shutil.copy2(src, STAGING / name)
            copied += 1
    return copied


def copy_package_dirs() -> int:
    """Copy .py files from each package dir (no __pycache__). Returns count."""
    copied = 0
    for dirname in PACKAGE_DIRS:
        src_dir = REPO_ROOT / dirname
        if not src_dir.is_dir():
            fail(f"required package dir missing: {dirname}")
        for py_file in sorted(src_dir.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            rel = py_file.relative_to(REPO_ROOT)
            dest = STAGING / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py_file, dest)
            copied += 1
    return copied


def assert_no_leaks() -> None:
    """Hard-fail if secrets or build junk landed in staging."""
    forbidden_names = {".env", ".venv", "__pycache__", "tests"}
    for path in STAGING.rglob("*"):
        if path.name in forbidden_names:
            fail(f"forbidden path leaked into staging: {path}")


def read_manifest_version() -> str:
    import json

    data = json.loads((STAGING / "manifest.json").read_text(encoding="utf-8"))
    return str(data["version"])


def read_pyproject_version() -> str:
    data = tomllib.loads((STAGING / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def read_main_version() -> str:
    text = (REPO_ROOT / "personal_mcp_servicenow_main.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        fail("could not find __version__ in personal_mcp_servicenow_main.py")
    return match.group(1)


def assert_versions_aligned() -> str:
    """Ensure all three version sources agree. Returns the version."""
    manifest_v = read_manifest_version()
    pyproject_v = read_pyproject_version()
    main_v = read_main_version()
    if not (manifest_v == pyproject_v == main_v):
        fail(
            "version mismatch: "
            f"manifest={manifest_v}, pyproject={pyproject_v}, __version__={main_v}"
        )
    return manifest_v


def resolve_mcpb() -> str:
    """Resolve the mcpb CLI (mcpb / mcpb.cmd on Windows) or fail."""
    exe = shutil.which("mcpb") or shutil.which("mcpb.cmd")
    if not exe:
        fail(
            "mcpb CLI not found on PATH. Install it with:\n"
            "    npm install -g @anthropic-ai/mcpb"
        )
    return exe


def run_mcpb(mcpb: str, version: str) -> Path:
    """Validate the staged manifest then pack the bundle. Returns bundle path."""
    manifest = STAGING / "manifest.json"
    bundle = REPO_ROOT / "dist" / f"personal-mcp-servicenow-{version}.mcpb"

    validate = subprocess.run([mcpb, "validate", str(manifest)])
    if validate.returncode != 0:
        sys.exit(validate.returncode)

    pack = subprocess.run([mcpb, "pack", str(STAGING), str(bundle)])
    if pack.returncode != 0:
        sys.exit(pack.returncode)

    return bundle


def main() -> int:
    clean_staging()
    root_count = copy_root_files()
    pkg_count = copy_package_dirs()
    assert_no_leaks()
    version = assert_versions_aligned()

    print(f"Staged {root_count} root files + {pkg_count} package files")
    print(f"Version: {version}")

    mcpb = resolve_mcpb()
    bundle = run_mcpb(mcpb, version)

    size_kb = bundle.stat().st_size / 1024
    print(f"Bundle: {bundle}  ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
