"""Tests for CLI argument handling."""
import subprocess
import sys


def test_version_flag():
    """--version should print version and exit 0."""
    result = subprocess.run(
        [sys.executable, 'personal_mcp_servicenow_main.py', '--version'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert 'mcp-servicenow' in result.stdout.lower() or '2.0.0' in result.stdout


def test_help_flag():
    """--help should print usage and exit 0."""
    result = subprocess.run(
        [sys.executable, 'personal_mcp_servicenow_main.py', '--help'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert 'usage' in result.stdout.lower() or '--version' in result.stdout
