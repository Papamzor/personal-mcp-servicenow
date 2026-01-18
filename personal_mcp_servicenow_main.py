#!/usr/bin/env python3
"""
MCP ServiceNow Server

A Model Context Protocol server for ServiceNow integration.
"""
import argparse
import getpass
import sys

__version__ = "2.2.0"


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
        config['client_secret'] = getpass.getpass("OAuth Client Secret: ").strip()
    else:
        config['auth_type'] = 'basic'
        config['username'] = input("Username: ").strip()
        config['password'] = getpass.getpass("Password: ").strip()

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
