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
