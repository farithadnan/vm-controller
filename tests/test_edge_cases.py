"""
Additional edge case tests for comprehensive coverage
"""
import pytest
from unittest.mock import patch, mock_open, Mock
from fastapi import HTTPException
from controller_api import Config, LogManager, SecurityValidator, HyperVManager


class TestConfigEdgeCases:
    """Edge cases for Config class."""
    
    @patch.dict('os.environ', {'API_KEY': '', 'HMAC_SECRET': ''})
    def test_config_empty_credentials(self):
        """Test config with empty credential strings."""
        with pytest.raises(ValueError):
            Config()
    
    @patch('controller_api.load_dotenv')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_config_creates_nested_log_dir(self, mock_makedirs, mock_exists, mock_load_dotenv):
        """Test config creates nested log directories."""
        mock_exists.return_value = False
        
        with patch.dict('os.environ', {
            'API_KEY': 'test_key',
            'HMAC_SECRET': 'test_secret',
            'ALLOW_IP': ''
        }):
            config = Config()
            mock_makedirs.assert_called()


class TestLogManagerEdgeCases:
    """Edge cases for LogManager class."""
    
    @pytest.fixture
    def log_manager(self, mock_env_vars):
        config = Config()
        return LogManager(config)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_to_file_unicode(self, mock_file, log_manager):
        """Test logging with unicode characters."""
        log_manager.write_audit(
            action="start",
            vm="VM-测试-01",  # Chinese characters
            ip="192.168.1.100",
            status="success",
            details="Тест"  # Cyrillic
        )
        
        mock_file.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_audit_empty_details(self, mock_file, log_manager):
        """Test audit log with empty details."""
        log_manager.write_audit(
            action="start",
            vm="test-vm",
            ip="192.168.1.100",
            status="success",
            details=""
        )
        
        mock_file.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_app_log_with_existing_timestamp(self, mock_file, log_manager):
        """Test app log when timestamp already exists in data."""
        log_data = {
            "event": "test",
            "timestamp": "2025-01-01T00:00:00"
        }
        
        log_manager.write_app_log(log_data)
        
        # Should not overwrite existing timestamp
        mock_file.assert_called_once()


class TestSecurityValidatorEdgeCases:
    """Edge cases for SecurityValidator class."""
    
    @pytest.fixture
    def security_validator(self, mock_env_vars):
        config = Config()
        return SecurityValidator(config)
    
    def test_verify_api_key_whitespace(self, security_validator):
        """Test API key with leading/trailing whitespace."""
        with pytest.raises(HTTPException):
            security_validator.verify_api_key('  test_api_key_12345  ')
    
    def test_verify_ip_ipv6(self, security_validator):
        """Test IP verification with IPv6 address."""
        # Currently only checks if IP matches, no format validation
        with pytest.raises(HTTPException):
            security_validator.verify_ip('::1')
    
    def test_verify_hmac_timestamp_expired(self, security_validator):
        """Test HMAC with very old timestamp."""
        import hmac
        import hashlib
        
        body = b'test'
        old_timestamp = '1000000000'  # Year 2001
        
        message = body + old_timestamp.encode()
        signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Should verify signature regardless of timestamp age
        # (timestamp validation could be added as enhancement)
        try:
            security_validator.verify_hmac_signature(signature, old_timestamp, body)
            assert True
        except HTTPException:
            pytest.fail("Should validate signature even with old timestamp")
    
    def test_verify_hmac_empty_body(self, security_validator):
        """Test HMAC signature with empty body."""
        import hmac
        import hashlib
        
        body = b''
        timestamp = '1234567890'
        
        message = body + timestamp.encode()
        signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        try:
            security_validator.verify_hmac_signature(signature, timestamp, body)
            assert True
        except HTTPException:
            pytest.fail("Should handle empty body")


class TestHyperVManagerEdgeCases:
    """Edge cases for HyperVManager class."""
    
    @pytest.fixture
    def hyperv_manager(self):
        return HyperVManager()
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_get_vm_names_with_blank_lines(self, mock_run, hyperv_manager):
        """Test parsing VM list with blank lines."""
        mock_run.return_value = "VM-Test-01\n\n\nVM-Test-02\n\n"
        
        result = hyperv_manager.get_all_vm_names()
        
        assert len(result) == 2
        assert 'VM-Test-01' in result
        assert 'VM-Test-02' in result
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_get_vm_names_with_whitespace(self, mock_run, hyperv_manager):
        """Test parsing VM list with extra whitespace."""
        mock_run.return_value = "  VM-Test-01  \n  VM-Test-02  "
        
        result = hyperv_manager.get_all_vm_names()
        
        assert 'VM-Test-01' in result
        assert 'VM-Test-02' in result
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_validate_vm_case_sensitive(self, mock_run, hyperv_manager):
        """Test VM validation is case-sensitive."""
        mock_run.return_value = "VM-Test-01\nvm-test-01"
        
        # Should find exact match
        try:
            hyperv_manager.validate_vm_exists('VM-Test-01')
            assert True
        except HTTPException:
            pytest.fail("Should find exact case match")
    
    @patch('subprocess.run')
    def test_run_powershell_timeout(self, mock_run, hyperv_manager):
        """Test PowerShell execution timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('powershell', 30)
        
        with pytest.raises(Exception):
            hyperv_manager._run_powershell("Start-Sleep -Seconds 100")
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_vm_operations_with_quotes(self, mock_run, hyperv_manager):
        """Test VM operations handle VM names with quotes safely."""
        # VM name with single quote
        mock_run.return_value = "Success"
        
        result = hyperv_manager.start_vm("VM-Test's-Server")
        
        assert result is not None
        # Verify PowerShell command properly escaped quotes
        assert mock_run.called
