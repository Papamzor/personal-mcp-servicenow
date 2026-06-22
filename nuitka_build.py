#!/usr/bin/env python3
"""
Nuitka build script for MCP ServiceNow.

Usage:
    python nuitka_build.py           # Build for current platform
    python nuitka_build.py --test    # Build and run smoke test
"""
import subprocess
import sys
import platform
import os
import argparse

_PROJECT_ROOT = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))


def _validate_path(path: str) -> str:
    """Resolve path and raise ValueError if it escapes the project root."""
    if os.path.isabs(path):
        resolved = os.path.realpath(path)
    else:
        resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, path))
    if resolved != _PROJECT_ROOT and not resolved.startswith(_PROJECT_ROOT + os.sep):
        raise ValueError(f"Path traversal rejected: {path!r} escapes project root")
    return resolved


def get_output_name():
    """Get platform-appropriate output filename."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ('x86_64', 'amd64'):
        arch = 'amd64'
    elif machine in ('arm64', 'aarch64'):
        arch = 'arm64'
    else:
        arch = machine

    # Normalize OS names
    if system == 'darwin':
        os_name = 'darwin'
    elif system == 'windows':
        os_name = 'windows'
    else:
        os_name = 'linux'

    name = f"mcp-servicenow-{os_name}-{arch}"
    if system == 'windows':
        name += '.exe'

    return name


def build(output_dir='dist'):
    """Run Nuitka build."""
    import sysconfig

    safe_output_dir = _validate_path(output_dir)
    output_name = get_output_name()
    output_path = os.path.join(safe_output_dir, output_name)

    os.makedirs(safe_output_dir, exist_ok=True)

    cmd = [
        sys.executable, '-m', 'nuitka',
        '--standalone',
        '--onefile',
        f'--output-filename={output_name}',
        f'--output-dir={safe_output_dir}',
        '--assume-yes-for-downloads',  # Auto-download dependencies
        '--remove-output',  # Clean up build artifacts
        'personal_mcp_servicenow_main.py'
    ]

    print(f"Building {output_name}...")
    print(f"Command: {' '.join(cmd)}")
    print()

    # Set PYTHONHOME to help Nuitka find libpython on Python Build Standalone
    env = os.environ.copy()
    env['PYTHONHOME'] = sys.base_prefix
    print(f"Using PYTHONHOME={sys.base_prefix}")

    result = subprocess.run(cmd, env=env)

    if result.returncode != 0:
        print(f"Build failed with exit code {result.returncode}")
        sys.exit(1)

    print(f"\nBuild complete: {output_path}")
    return output_path


def smoke_test(binary_path):
    """Run smoke test on built binary."""
    safe_binary = _validate_path(binary_path)
    if not os.path.isfile(safe_binary):
        raise FileNotFoundError(f"Binary not found: {safe_binary!r}")

    print(f"\nRunning smoke test on {safe_binary}...")

    # Test --version
    result = subprocess.run([safe_binary, '--version'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL: --version returned {result.returncode}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)

    print(f"  --version: {result.stdout.strip()}")

    # Test --help
    result = subprocess.run([safe_binary, '--help'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL: --help returned {result.returncode}")
        sys.exit(1)

    print("  --help: OK")
    print("\nSmoke test passed!")


def main():
    parser = argparse.ArgumentParser(description='Build MCP ServiceNow binary')
    parser.add_argument('--test', action='store_true', help='Run smoke test after build')
    parser.add_argument('--output-dir', default='dist', help='Output directory')
    args = parser.parse_args()

    binary_path = build(args.output_dir)

    if args.test:
        smoke_test(binary_path)


if __name__ == '__main__':
    main()
