# MCPB Bundle — Build & Release Guide

IT / maintainer-facing documentation for the Claude Desktop Extension (`.mcpb`) build and release process. For the business-user install steps, see the [README](../README.md#easy-install--claude-desktop-no-technical-knowledge-needed).

## What the bundle is

A `.mcpb` file is a zip archive containing `manifest.json` plus the server's Python source, built with the `mcpb` CLI (`@anthropic-ai/mcpb` on npm). The manifest is schema version 0.4 and declares `server.type: "uv"` — Claude Desktop itself manages the Python runtime, resolving and installing dependencies from `pyproject.toml` at install time / on first launch, so no bundled interpreter or vendored `site-packages` ships inside the archive.

## Prerequisites

- Python 3.11+
- Node 20+
- `mcpb` CLI: `npm install -g @anthropic-ai/mcpb`

## Local build

```bash
python scripts/build_mcpb.py
```

What it does:

1. Cleans and recreates `dist/mcpb-staging/`.
2. Copies a fixed whitelist of root files (`personal_mcp_servicenow_main.py`, `tools.py`, `constants.py`, `config_loader.py`, `utils.py`, `utility_tools.py`, `audit_middleware.py`, `auth_middleware.py`, `param_coercion.py`, `manifest.json`, `pyproject.toml`, `LICENSE`, plus `icon.png` if present) and whole package directories (`Table_Tools`, `filter`, `http_layer`, `oauth`) into staging — never packs from the repo root directly, since a live `.env` with real secrets lives there.
3. Asserts no secrets or build junk (`.env`, `.venv`, `__pycache__`, `tests`) leaked into staging.
4. Checks that the version in `manifest.json`, `pyproject.toml`, and `personal_mcp_servicenow_main.py` all agree; fails hard on mismatch.
5. Runs `mcpb validate` against the staged manifest, then `mcpb pack` to produce the bundle.

Output: `dist/personal-mcp-servicenow-<version>.mcpb`

## Release procedure

1. Bump the version in all three places (they must stay in sync):
   - `manifest.json` (`version`)
   - `pyproject.toml` (`[project].version`)
   - `personal_mcp_servicenow_main.py` (`__version__`)
2. Commit the version bump.
3. Tag it: `git tag v<X.Y.Z>`
4. Push the tag to the GitHub remote (`Papamzor/personal-mcp-servicenow`) — this is the remote GitHub Actions releases from, separate from the Bitbucket `origin` remote used for CI.
5. `.github/workflows/release.yaml` builds the `.mcpb` bundle and attaches it to the GitHub Release.

`tests/test_pyproject_sync.py` enforces the three-way version alignment in CI — a mismatched bump fails the build before it ever reaches the tag/push step.

## Configuration mapping

`manifest.json` maps each `user_config` field a business user fills in to an environment variable the server reads. Two more env vars are hardcoded (not user-configurable) since this bundle only supports one auth type and one transport.

| user_config field | Env var | Notes |
|---|---|---|
| `servicenow_instance` | `SERVICENOW_INSTANCE` | e.g. `https://company.service-now.com` |
| `client_id` | `SERVICENOW_CLIENT_ID` | |
| `client_secret` | `SERVICENOW_CLIENT_SECRET` | `sensitive: true` — Claude Desktop stores it in the OS credential store (Windows Credential Manager / macOS Keychain), never in plain text on disk |
| — | `SERVICENOW_AUTH_TYPE` | hardcoded `"oauth"` |
| — | `MCP_TRANSPORT` | hardcoded `"stdio"` |

## Corporate network considerations

On first launch, Claude Desktop (via `uv`) resolves and downloads the server's dependencies from PyPI. On a locked-down corporate network this requires one of:

- Allowlisting `pypi.org`, `files.pythonhosted.org`, and `astral.sh` at the firewall/proxy, or
- Pointing `UV_INDEX_URL` at an internal package mirror, combined with `HTTP_PROXY` / `HTTPS_PROXY` set system-wide, so `uv` resolves through the mirror instead of the public index.

This is a one-time cost per machine — subsequent launches reuse the already-installed environment.

## Fallback: central SSE hosting

If a business's deployed Claude Desktop version doesn't support `uv`-type extensions (or the `.mcpb` install path is otherwise blocked by policy), fall back to hosting the server centrally over SSE and pointing Claude Code / Claude Desktop at it as a remote MCP server. See the README's [Azure Container Apps + Key Vault](../README.md#cloud-hosting-azure-container-apps--key-vault) section for the production deployment pattern.

## ServiceNow-side prerequisite

The 3 values IT hands to business users (instance address, Client ID, Client Secret) come from a ServiceNow OAuth client created ahead of rollout. See [OAUTH_SETUP_GUIDE.md](../OAUTH_SETUP_GUIDE.md) for how to create it.
