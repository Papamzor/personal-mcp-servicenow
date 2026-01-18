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
