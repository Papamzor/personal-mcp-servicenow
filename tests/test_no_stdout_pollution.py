"""Lint guard: server runtime code must never print to stdout.

MCP stdio transport reserves stdout for JSON-RPC frames. Any stray
``print(...)`` without ``file=sys.stderr`` corrupts the frame stream and
the client raises ``Unexpected non-whitespace character after JSON at
position N``. This test parses every runtime module's AST and asserts
each ``print`` call is explicitly routed to ``sys.stderr``.

Excluded paths:
- ``.venv/``, ``graphify-out/``, ``docs/``, ``tests/`` — not in the server runtime
- ``scripts/`` — local benchmarking/utility scripts
- ``nuitka_build.py`` — build harness
- ``personal_mcp_servicenow_main.py`` — CLI setup wizard, runs before stdio takeover
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".venv", "graphify-out", "docs", "tests", "scripts", "v3.0", "v4.0"}
EXCLUDED_FILES = {"nuitka_build.py", "personal_mcp_servicenow_main.py"}


def _is_stderr_target(file_kwarg: ast.expr) -> bool:
    """True when the ``file=`` argument resolves to ``sys.stderr``."""
    if not isinstance(file_kwarg, ast.Attribute):
        return False
    if file_kwarg.attr != "stderr":
        return False
    return isinstance(file_kwarg.value, ast.Name) and file_kwarg.value.id == "sys"


def _find_offending_prints(path: Path) -> List[Tuple[int, str]]:
    """Return (lineno, source-snippet) for every print call in *path* not routed to stderr."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    offenders: List[Tuple[int, str]] = []
    src_lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "print"):
            continue

        file_kwarg = next(
            (kw.value for kw in node.keywords if kw.arg == "file"),
            None,
        )
        if file_kwarg is None or not _is_stderr_target(file_kwarg):
            snippet = src_lines[node.lineno - 1].strip() if node.lineno - 1 < len(src_lines) else ""
            offenders.append((node.lineno, snippet))

    return offenders


def _iter_runtime_modules() -> List[Path]:
    paths: List[Path] = []
    for path in REPO_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDED_FILES:
            continue
        paths.append(path)
    return paths


def test_no_runtime_module_prints_to_stdout():
    """Every print in the server runtime must be routed to sys.stderr."""
    violations: List[str] = []
    for path in _iter_runtime_modules():
        for lineno, snippet in _find_offending_prints(path):
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel.as_posix()}:{lineno}: {snippet}")

    assert not violations, (
        "Stray stdout print(...) in server runtime — these corrupt the MCP "
        "stdio frame stream. Add file=sys.stderr or remove the call.\n  "
        + "\n  ".join(violations)
    )


def test_lint_guard_actually_detects_pollution(tmp_path):
    """Self-check: the AST scanner must catch a known-bad print."""
    bad = tmp_path / "bad.py"
    bad.write_text("print('this would corrupt stdio')\n", encoding="utf-8")
    assert _find_offending_prints(bad), "AST scanner failed to flag a bare print()"


def test_lint_guard_accepts_stderr_print(tmp_path):
    """Self-check: the AST scanner must NOT flag stderr-routed prints."""
    good = tmp_path / "good.py"
    good.write_text("import sys\nprint('safe diagnostic', file=sys.stderr)\n", encoding="utf-8")
    assert not _find_offending_prints(good), "AST scanner false-positive on sys.stderr print"
