#!/usr/bin/env python3
"""
MCP ServiceNow Server

A Model Context Protocol server for ServiceNow integration.
"""
import argparse
import getpass
import sys

import structlog

# Configure structlog once at the entry point so every module that calls
# structlog.get_logger() emits JSON to stderr (Azure Monitor ingests it
# automatically from Container Apps / ACI stdout/stderr).
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

__version__ = "4.4.0"


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

    print("\nAuthentication: OAuth 2.0 client credentials (only supported method).")
    config['auth_type'] = 'oauth'
    config['client_id'] = input("OAuth Client ID: ").strip()
    config['client_secret'] = getpass.getpass("OAuth Client Secret: ").strip()

    save_config(config)
    print(f"\nConfiguration saved to: {get_config_file_path()}")
    print("You can now use mcp-servicenow in your Claude Code configuration.")


def main():
    """Main entry point."""
    args = parse_args()

    if args.setup:
        run_setup()
        sys.exit(0)

    # Normal server startup - transport is controlled by MCP_TRANSPORT env var
    # stdio (default): local use with Claude Code
    # sse: cloud/Docker hosting for network-accessible agents (N8N, etc.)
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "sse":
        insecure = os.environ.get("MCP_ALLOW_INSECURE_SSE", "").strip().lower() in ("1", "true", "yes", "on")
        if not os.environ.get("MCP_SSE_AUTH_TOKEN") and not insecure:
            print(
                "Refusing to start SSE transport without MCP_SSE_AUTH_TOKEN. "
                "Set it, or set MCP_ALLOW_INSECURE_SSE=true to override.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Personal ServiceNow MCP Server started (SSE)", file=sys.stderr)
        from tools import mcp
        mcp.run(transport="sse")
    else:
        print("Personal ServiceNow MCP Server started (stdio).", file=sys.stderr)
        from tools import mcp
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
