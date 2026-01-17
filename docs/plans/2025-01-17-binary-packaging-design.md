# MCP ServiceNow Binary Packaging Design

**Date:** 2025-01-17
**Status:** Approved
**Author:** David Vasandani + Claude

## Overview

Package the MCP ServiceNow server as standalone binaries for internal distribution, eliminating the need for Python environment setup on colleague machines.

## Requirements

| Requirement | Decision |
|-------------|----------|
| Target audience | Internal team only |
| Platforms | macOS (Intel + ARM), Linux, Windows |
| Configuration | Environment variables + config file (env vars take precedence) |
| Distribution | GitHub Releases (private repo) |
| Priority | Fastest startup time |

## Tool Selection: Nuitka

Selected **Nuitka** over alternatives (PyInstaller, PyOxidizer) for:

- **Fastest startup** (~50-100ms) - compiles Python to native C code
- **No extraction step** - true native binary, not a bundled archive
- **Cross-platform support** - builds on all target platforms

Trade-offs accepted:
- Longer build times (5-10 min per platform) - acceptable for CI
- Larger binaries (~50-80MB) - acceptable for internal use

## Project Structure

```
mcp-servicenow/
├── build/                     # Build artifacts (gitignored)
├── dist/                      # Final binaries (gitignored)
├── nuitka_build.py           # Cross-platform build script
├── config_loader.py          # Flexible config handling
├── .github/
│   └── workflows/
│       └── release.yaml      # CI/CD for multi-platform builds
└── (existing files unchanged)
```

## Configuration

### Config File Location

| Platform | Path |
|----------|------|
| macOS/Linux | `~/.config/mcp-servicenow/config.json` |
| Windows | `%APPDATA%\mcp-servicenow\config.json` |

### Config File Format

```json
{
  "instance": "your-instance.service-now.com",
  "auth_type": "oauth",

  "client_id": "...",
  "client_secret": "...",

  "username": "...",
  "password": "..."
}
```

### Environment Variable Mapping

| Environment Variable | Config Key |
|---------------------|------------|
| `SERVICENOW_INSTANCE` | instance |
| `SERVICENOW_AUTH_TYPE` | auth_type |
| `SERVICENOW_CLIENT_ID` | client_id |
| `SERVICENOW_CLIENT_SECRET` | client_secret |
| `SERVICENOW_USERNAME` | username |
| `SERVICENOW_PASSWORD` | password |

### Resolution Priority

1. Environment variables (highest priority)
2. Config file
3. Error with setup instructions

## CI/CD Pipeline

### Trigger

```bash
git tag v1.0.0 && git push --tags
```

### Build Matrix

| Platform | Runner | Output |
|----------|--------|--------|
| macOS Intel | macos-latest | `mcp-servicenow-darwin-amd64` |
| macOS ARM | macos-latest | `mcp-servicenow-darwin-arm64` |
| Linux | ubuntu-latest | `mcp-servicenow-linux-amd64` |
| Windows | windows-latest | `mcp-servicenow-windows-amd64.exe` |

### Workflow Steps

1. Checkout code
2. Set up Python 3.11
3. Install dependencies + Nuitka
4. Run Nuitka build
5. Upload binary as release asset

### Build Time

~10-15 minutes total (parallel jobs)

## User Installation

### Steps

1. Download binary from GitHub Releases
2. Make executable: `chmod +x mcp-servicenow-darwin-arm64`
3. Move to PATH: `mv mcp-servicenow-* /usr/local/bin/mcp-servicenow`
4. Run setup: `mcp-servicenow --setup`

### Claude Code Configuration

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "/usr/local/bin/mcp-servicenow"
    }
  }
}
```

Or with inline env vars:

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "/usr/local/bin/mcp-servicenow",
      "env": {
        "SERVICENOW_INSTANCE": "sweetgreen.service-now.com",
        "SERVICENOW_AUTH_TYPE": "oauth",
        "SERVICENOW_CLIENT_ID": "...",
        "SERVICENOW_CLIENT_SECRET": "..."
      }
    }
  }
}
```

## CLI Flags

| Flag | Description |
|------|-------------|
| `--version` | Print version and exit |
| `--setup` | Interactive setup wizard |
| (none) | Run MCP server (default) |

## Testing

### Local Build Test

```bash
pip install nuitka

python -m nuitka --standalone --onefile \
  --output-filename=mcp-servicenow-test \
  personal_mcp_servicenow_main.py

./mcp-servicenow-test --version
./mcp-servicenow-test --setup
```

### CI Validation

1. Smoke test: Binary runs and prints version
2. Config test: `--setup` flag works
3. Size check: Warn if binary exceeds 100MB

## Pre-Release Checklist

- [ ] Local build works
- [ ] All tests pass in CI
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] Tag pushed

## Files to Create/Modify

| File | Action |
|------|--------|
| `config_loader.py` | Create - flexible credential loading |
| `nuitka_build.py` | Create - local build helper |
| `.github/workflows/release.yaml` | Create - multi-platform CI/CD |
| `personal_mcp_servicenow_main.py` | Modify - add --version, --setup flags |
| `README.md` | Modify - add installation instructions |
| `.gitignore` | Modify - add build/, dist/ |
