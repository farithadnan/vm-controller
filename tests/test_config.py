"""
Tests for Configuration class
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from controller_api import Config


class TestConfig:
    """Test suite for Config class."""
    
    def test_config_loads_env_variables(self, mock_env_vars):
        """Test that config loads environment variables correctly."""
        config = Config()
        
        assert config.api_key == 'test_api_key_12345'
        assert config.hmac_secret == 'test_hmac_secret_67890'
        assert config.allow_ip == '192.168.1.100'
        assert config.log_dir == 'logs'
    
    def test_config_without_ip_restriction(self, mock_env_vars_no_ip):
        """Test config when ALLOW_IP is empty."""
        config = Config()
        
        assert config.api_key == 'test_api_key_12345'
        assert config.hmac_secret == 'test_hmac_secret_67890'
        assert config.allow_ip == ''
    
    def test_config_validates_api_key(self):
        """Test that config raises error when API_KEY is missing."""
        with patch.dict(os.environ, {'API_KEY': '', 'HMAC_SECRET': 'test_secret'}):
            with pytest.raises(ValueError, match="API_KEY must be set"):
                Config()
    
    def test_config_validates_hmac_secret(self):
        """Test that config raises error when HMAC_SECRET is missing."""
        with patch.dict(os.environ, {'API_KEY': 'test_key', 'HMAC_SECRET': ''}):
            with pytest.raises(ValueError, match="HMAC_SECRET must be set"):
                Config()
    
    @patch('os.makedirs')
    def test_config_creates_log_directory(self, mock_makedirs, mock_env_vars):
        """Test that config creates logs directory if it doesn't exist."""
        with patch('os.path.exists', return_value=False):
            config = Config()
            mock_makedirs.assert_called_once_with('logs')
    
    def test_config_log_paths(self, mock_env_vars):
        """Test that log paths are correctly constructed."""
        config = Config()
        
        assert config.audit_log_path == os.path.join('logs', 'audit.log')
        assert config.app_log_path == os.path.join('logs', 'app.log')
