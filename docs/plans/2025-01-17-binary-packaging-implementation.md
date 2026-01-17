# Binary Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Package the MCP ServiceNow server as standalone binaries for internal cross-platform distribution using Nuitka.

**Architecture:** Add a config loader that supports both environment variables and config files (env vars take precedence). Add CLI flags for --version and --setup. Create GitHub Actions workflow for multi-platform builds via Nuitka.

**Tech Stack:** Python 3.11, Nuitka, GitHub Actions

---

## Task 1: Update .gitignore for Build Artifacts

**Files:**
- Modify: `.gitignore`

**Step 1: Add build directories to .gitignore**

Add these lines to `.gitignore`:

```
# Nuitka build artifacts
build/
dist/
*.build/
*.dist/
*.onefile-build/
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add Nuitka build directories to gitignore"
```

---

## Task 2: Create Config Loader Module

**Files:**
- Create: `config_loader.py`
- Create: `tests/test_config_loader.py`

**Step 1: Write the failing test for config loading**

Create `tests/test_config_loader.py`:

```python
"""Tests for config_loader module."""
import os
import json
import tempfile
import pytest
from unittest.mock import patch


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    @patch('platform.system', return_value='Darwin')
    def test_macos_config_dir(self, mock_system):
        from config_loader import get_config_dir
        result = get_config_dir()
        assert '.config/mcp-servicenow' in result

    @patch('platform.system', return_value='Windows')
    @patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'})
    def test_windows_config_dir(self, mock_system):
        from config_loader import get_config_dir
        result = get_config_dir()
        assert 'mcp-servicenow' in result


class TestLoadConfig:
    """Tests for load_config function."""

    def test_env_vars_take_precedence(self):
        """Environment variables should override config file."""
        from config_loader import load_config

        with patch.dict(os.environ, {
            'SERVICENOW_INSTANCE': 'env-instance.service-now.com',
            'SERVICENOW_AUTH_TYPE': 'basic',
            'SERVICENOW_USERNAME': 'env-user',
            'SERVICENOW_PASSWORD': 'env-pass'
        }):
            config = load_config()
            assert config['instance'] == 'env-instance.service-now.com'
            assert config['auth_type'] == 'basic'
            assert config['username'] == 'env-user'

    def test_config_file_loading(self):
        """Should load from config file when env vars not set."""
        from config_loader import load_config, get_config_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('config_loader.get_config_dir', return_value=tmpdir):
                config_file = os.path.join(tmpdir, 'config.json')
                with open(config_file, 'w') as f:
                    json.dump({
                        'instance': 'file-instance.service-now.com',
                        'auth_type': 'oauth',
                        'client_id': 'file-client-id',
                        'client_secret': 'file-secret'
                    }, f)

                with patch.dict(os.environ, {}, clear=True):
                    # Clear any SERVICENOW_ env vars
                    env_copy = {k: v for k, v in os.environ.items()
                               if not k.startswith('SERVICENOW_')}
                    with patch.dict(os.environ, env_copy, clear=True):
                        config = load_config()
                        assert config['instance'] == 'file-instance.service-now.com'


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_oauth_config(self):
        from config_loader import validate_config
        config = {
            'instance': 'test.service-now.com',
            'auth_type': 'oauth',
            'client_id': 'abc123',
            'client_secret': 'secret'
        }
        # Should not raise
        validate_config(config)

    def test_valid_basic_config(self):
        from config_loader import validate_config
        config = {
            'instance': 'test.service-now.com',
            'auth_type': 'basic',
            'username': 'user',
            'password': 'pass'
        }
        # Should not raise
        validate_config(config)

    def test_missing_instance_raises(self):
        from config_loader import validate_config, ConfigError
        config = {
            'auth_type': 'basic',
            'username': 'user',
            'password': 'pass'
        }
        with pytest.raises(ConfigError, match='instance'):
            validate_config(config)

    def test_oauth_missing_client_id_raises(self):
        from config_loader import validate_config, ConfigError
        config = {
            'instance': 'test.service-now.com',
            'auth_type': 'oauth',
            'client_secret': 'secret'
        }
        with pytest.raises(ConfigError, match='client_id'):
            validate_config(config)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_loader.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'config_loader'"

**Step 3: Write the config_loader implementation**

Create `config_loader.py`:

```python
"""
Configuration loader for MCP ServiceNow.

Supports loading credentials from:
1. Environment variables (highest priority)
2. Config file (~/.config/mcp-servicenow/config.json on Unix, %APPDATA% on Windows)

Environment variables:
- SERVICENOW_INSTANCE: ServiceNow instance URL
- SERVICENOW_AUTH_TYPE: 'oauth' or 'basic'
- SERVICENOW_CLIENT_ID: OAuth client ID
- SERVICENOW_CLIENT_SECRET: OAuth client secret
- SERVICENOW_USERNAME: Basic auth username
- SERVICENOW_PASSWORD: Basic auth password
"""
import os
import json
import platform
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def get_config_dir() -> str:
    """Get the configuration directory path based on platform."""
    system = platform.system()

    if system == 'Windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, 'mcp-servicenow')
    else:
        # macOS and Linux
        return os.path.join(os.path.expanduser('~'), '.config', 'mcp-servicenow')


def get_config_file_path() -> str:
    """Get the full path to the config file."""
    return os.path.join(get_config_dir(), 'config.json')


def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}

    env_mapping = {
        'SERVICENOW_INSTANCE': 'instance',
        'SERVICENOW_AUTH_TYPE': 'auth_type',
        'SERVICENOW_CLIENT_ID': 'client_id',
        'SERVICENOW_CLIENT_SECRET': 'client_secret',
        'SERVICENOW_USERNAME': 'username',
        'SERVICENOW_PASSWORD': 'password',
    }

    for env_var, config_key in env_mapping.items():
        value = os.environ.get(env_var)
        if value:
            config[config_key] = value

    return config


def load_config_from_file() -> Dict[str, Any]:
    """Load configuration from config file."""
    config_path = get_config_file_path()

    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise ConfigError(f"Failed to read config file: {e}")


def load_config() -> Dict[str, Any]:
    """
    Load configuration with priority:
    1. Environment variables (highest)
    2. Config file

    Returns merged configuration dictionary.
    """
    # Start with file config as base
    config = load_config_from_file()

    # Override with environment variables
    env_config = load_config_from_env()
    config.update(env_config)

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration is complete.

    Raises:
        ConfigError: If required fields are missing.
    """
    if not config.get('instance'):
        raise ConfigError(
            "Missing 'instance'. Set SERVICENOW_INSTANCE env var or add to config file."
        )

    auth_type = config.get('auth_type', 'basic')

    if auth_type == 'oauth':
        if not config.get('client_id'):
            raise ConfigError(
                "OAuth requires 'client_id'. Set SERVICENOW_CLIENT_ID env var or add to config file."
            )
        if not config.get('client_secret'):
            raise ConfigError(
                "OAuth requires 'client_secret'. Set SERVICENOW_CLIENT_SECRET env var or add to config file."
            )
    else:
        # basic auth
        if not config.get('username'):
            raise ConfigError(
                "Basic auth requires 'username'. Set SERVICENOW_USERNAME env var or add to config file."
            )
        if not config.get('password'):
            raise ConfigError(
                "Basic auth requires 'password'. Set SERVICENOW_PASSWORD env var or add to config file."
            )


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config file."""
    config_dir = get_config_dir()
    os.makedirs(config_dir, exist_ok=True)

    config_path = get_config_file_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Set restrictive permissions on Unix
    if platform.system() != 'Windows':
        os.chmod(config_path, 0o600)


def get_setup_instructions() -> str:
    """Return setup instructions for users."""
    config_path = get_config_file_path()
    return f"""
MCP ServiceNow Configuration Required
=====================================

Option 1: Environment Variables
-------------------------------
Set these environment variables:
  SERVICENOW_INSTANCE=your-instance.service-now.com
  SERVICENOW_AUTH_TYPE=oauth  (or 'basic')

  For OAuth:
    SERVICENOW_CLIENT_ID=your-client-id
    SERVICENOW_CLIENT_SECRET=your-client-secret

  For Basic Auth:
    SERVICENOW_USERNAME=your-username
    SERVICENOW_PASSWORD=your-password

Option 2: Config File
---------------------
Create {config_path} with:

{{
  "instance": "your-instance.service-now.com",
  "auth_type": "oauth",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret"
}}

Option 3: Interactive Setup
---------------------------
Run: mcp-servicenow --setup
"""
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config_loader.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add config_loader.py tests/test_config_loader.py
git commit -m "feat: add config loader with env var and file support"
```

---

## Task 3: Add CLI Flags to Main Entry Point

**Files:**
- Modify: `personal_mcp_servicenow_main.py`
- Create: `tests/test_cli.py`

**Step 1: Write failing test for CLI flags**

Create `tests/test_cli.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL (--version not implemented)

**Step 3: Update main entry point with CLI flags**

Replace contents of `personal_mcp_servicenow_main.py`:

```python
#!/usr/bin/env python3
"""
MCP ServiceNow Server

A Model Context Protocol server for ServiceNow integration.
"""
import argparse
import sys

__version__ = "2.0.0"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='mcp-servicenow',
        description='MCP ServiceNow Server - ServiceNow integration for Claude'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'mcp-servicenow {__version__}'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run interactive setup wizard'
    )
    return parser.parse_args()


def run_setup():
    """Run interactive setup wizard."""
    from config_loader import save_config, get_config_file_path

    print("MCP ServiceNow Setup Wizard")
    print("=" * 40)
    print()

    config = {}

    config['instance'] = input("ServiceNow instance URL (e.g., company.service-now.com): ").strip()

    print("\nAuthentication type:")
    print("  1. OAuth (recommended)")
    print("  2. Basic auth")
    auth_choice = input("Choose [1/2]: ").strip()

    if auth_choice == '1':
        config['auth_type'] = 'oauth'
        config['client_id'] = input("OAuth Client ID: ").strip()
        config['client_secret'] = input("OAuth Client Secret: ").strip()
    else:
        config['auth_type'] = 'basic'
        config['username'] = input("Username: ").strip()
        config['password'] = input("Password: ").strip()

    save_config(config)
    print(f"\nConfiguration saved to: {get_config_file_path()}")
    print("You can now use mcp-servicenow in your Claude Code configuration.")


def main():
    """Main entry point."""
    args = parse_args()

    if args.setup:
        run_setup()
        sys.exit(0)

    # Normal server startup
    print("Personal ServiceNow MCP Server started.", file=sys.stderr)

    from tools import mcp
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add personal_mcp_servicenow_main.py tests/test_cli.py
git commit -m "feat: add --version and --setup CLI flags"
```

---

## Task 4: Create Local Build Script

**Files:**
- Create: `nuitka_build.py`

**Step 1: Create the build script**

Create `nuitka_build.py`:

```python
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
    output_name = get_output_name()
    output_path = os.path.join(output_dir, output_name)

    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        sys.executable, '-m', 'nuitka',
        '--standalone',
        '--onefile',
        f'--output-filename={output_name}',
        f'--output-dir={output_dir}',
        '--assume-yes-for-downloads',  # Auto-download dependencies
        '--remove-output',  # Clean up build artifacts
        'personal_mcp_servicenow_main.py'
    ]

    print(f"Building {output_name}...")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"Build failed with exit code {result.returncode}")
        sys.exit(1)

    print(f"\nBuild complete: {output_path}")
    return output_path


def smoke_test(binary_path):
    """Run smoke test on built binary."""
    print(f"\nRunning smoke test on {binary_path}...")

    # Test --version
    result = subprocess.run([binary_path, '--version'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL: --version returned {result.returncode}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)

    print(f"  --version: {result.stdout.strip()}")

    # Test --help
    result = subprocess.run([binary_path, '--help'], capture_output=True, text=True)
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
```

**Step 2: Make script executable and commit**

```bash
chmod +x nuitka_build.py
git add nuitka_build.py
git commit -m "feat: add local Nuitka build script"
```

---

## Task 5: Create GitHub Actions Release Workflow

**Files:**
- Create: `.github/workflows/release.yaml`

**Step 1: Create the workflow file**

Create `.github/workflows/release.yaml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build-macos:
    runs-on: macos-latest
    strategy:
      matrix:
        arch: [x86_64, arm64]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install nuitka

      - name: Build binary
        run: |
          if [ "${{ matrix.arch }}" = "arm64" ]; then
            ARCH_FLAG="--macos-target-arch=arm64"
          else
            ARCH_FLAG="--macos-target-arch=x86_64"
          fi

          python -m nuitka \
            --standalone \
            --onefile \
            --output-filename=mcp-servicenow-darwin-${{ matrix.arch }} \
            --output-dir=dist \
            --assume-yes-for-downloads \
            $ARCH_FLAG \
            personal_mcp_servicenow_main.py

      - name: Smoke test
        if: matrix.arch == 'arm64'  # Only test native arch
        run: |
          chmod +x dist/mcp-servicenow-darwin-${{ matrix.arch }}
          ./dist/mcp-servicenow-darwin-${{ matrix.arch }} --version

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: mcp-servicenow-darwin-${{ matrix.arch }}
          path: dist/mcp-servicenow-darwin-${{ matrix.arch }}

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install nuitka
          sudo apt-get update
          sudo apt-get install -y patchelf

      - name: Build binary
        run: |
          python -m nuitka \
            --standalone \
            --onefile \
            --output-filename=mcp-servicenow-linux-amd64 \
            --output-dir=dist \
            --assume-yes-for-downloads \
            personal_mcp_servicenow_main.py

      - name: Smoke test
        run: |
          chmod +x dist/mcp-servicenow-linux-amd64
          ./dist/mcp-servicenow-linux-amd64 --version

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: mcp-servicenow-linux-amd64
          path: dist/mcp-servicenow-linux-amd64

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install nuitka

      - name: Build binary
        run: |
          python -m nuitka `
            --standalone `
            --onefile `
            --output-filename=mcp-servicenow-windows-amd64.exe `
            --output-dir=dist `
            --assume-yes-for-downloads `
            personal_mcp_servicenow_main.py

      - name: Smoke test
        run: |
          .\dist\mcp-servicenow-windows-amd64.exe --version

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: mcp-servicenow-windows-amd64
          path: dist/mcp-servicenow-windows-amd64.exe

  release:
    needs: [build-macos, build-linux, build-windows]
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            artifacts/mcp-servicenow-darwin-x86_64/mcp-servicenow-darwin-x86_64
            artifacts/mcp-servicenow-darwin-arm64/mcp-servicenow-darwin-arm64
            artifacts/mcp-servicenow-linux-amd64/mcp-servicenow-linux-amd64
            artifacts/mcp-servicenow-windows-amd64/mcp-servicenow-windows-amd64.exe
          generate_release_notes: true
```

**Step 2: Commit**

```bash
mkdir -p .github/workflows
git add .github/workflows/release.yaml
git commit -m "feat: add GitHub Actions release workflow for multi-platform builds"
```

---

## Task 6: Update README with Installation Instructions

**Files:**
- Modify: `README.md`

**Step 1: Add installation section to README**

Add this section near the top of `README.md` (after the title/description):

```markdown
## Installation

### Option 1: Binary (Recommended)

Download the latest binary for your platform from [Releases](../../releases):

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon) | `mcp-servicenow-darwin-arm64` |
| macOS (Intel) | `mcp-servicenow-darwin-x86_64` |
| Linux | `mcp-servicenow-linux-amd64` |
| Windows | `mcp-servicenow-windows-amd64.exe` |

**macOS/Linux Setup:**
```bash
# Download and install
chmod +x mcp-servicenow-darwin-arm64
sudo mv mcp-servicenow-darwin-arm64 /usr/local/bin/mcp-servicenow

# Run setup wizard
mcp-servicenow --setup

# Verify
mcp-servicenow --version
```

**Windows Setup:**
```powershell
# Move to a directory in your PATH
Move-Item mcp-servicenow-windows-amd64.exe C:\Users\$env:USERNAME\AppData\Local\bin\mcp-servicenow.exe

# Run setup wizard
mcp-servicenow.exe --setup
```

### Claude Code Configuration

Add to your Claude Code MCP configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "/usr/local/bin/mcp-servicenow"
    }
  }
}
```

### Option 2: From Source

```bash
git clone <repo-url>
cd mcp-servicenow
pip install -r requirements.txt
python personal_mcp_servicenow_main.py
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add binary installation instructions to README"
```

---

## Task 7: Test Local Build

**Step 1: Install Nuitka**

```bash
pip install nuitka
```

**Step 2: Run local build with smoke test**

```bash
python nuitka_build.py --test
```

Expected output:
- Build completes successfully
- Binary created in `dist/`
- Smoke test passes (--version and --help work)

**Step 3: Commit any fixes if needed**

If build revealed issues, fix and commit them.

---

## Task 8: Create Release Tag

**Step 1: Verify all changes are committed**

```bash
git status
```

Expected: "nothing to commit, working tree clean"

**Step 2: Create and push tag**

```bash
git tag v2.0.0
git push origin feature/binary-packaging
git push origin v2.0.0
```

**Step 3: Verify GitHub Actions runs**

Go to GitHub repo → Actions tab → Verify "Build and Release" workflow starts.

---

## Summary

After completing all tasks, you will have:

1. A `config_loader.py` module for flexible credential management
2. CLI flags `--version` and `--setup` on the main entry point
3. A local build script `nuitka_build.py`
4. A GitHub Actions workflow that builds binaries for all platforms on tag push
5. Updated README with installation instructions
6. An initial v2.0.0 release with binaries

Colleagues can then download the binary, run `mcp-servicenow --setup`, and start using it with Claude Code.
