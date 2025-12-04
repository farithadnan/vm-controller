"""
Tests for SecurityValidator class
"""
import hmac
import hashlib
import pytest
from unittest.mock import Mock
from controller_api import Config, SecurityValidator


class TestSecurityValidator:
    """Test suite for SecurityValidator class."""
    
    @pytest.fixture
    def security_validator(self, mock_env_vars):
        """Create SecurityValidator instance for testing."""
        config = Config()
        return SecurityValidator(config)
    
    def test_verify_api_key_valid(self, security_validator):
        """Test API key verification with valid key."""
        result = security_validator.verify_api_key('test_api_key_12345')
        assert result is True
    
    def test_verify_api_key_invalid(self, security_validator):
        """Test API key verification with invalid key."""
        result = security_validator.verify_api_key('wrong_key')
        assert result is False
    
    def test_verify_api_key_none(self, security_validator):
        """Test API key verification with None."""
        result = security_validator.verify_api_key(None)
        assert result is False
    
    def test_verify_api_key_empty(self, security_validator):
        """Test API key verification with empty string."""
        result = security_validator.verify_api_key('')
        assert result is False
    
    def test_verify_hmac_signature_valid(self, security_validator):
        """Test HMAC signature verification with valid signature."""
        body = '{"vm_name": "test"}'
        timestamp = '1234567890'
        
        # Generate valid signature
        message = f"{body}{timestamp}"
        valid_signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = security_validator.verify_hmac_signature(body, timestamp, valid_signature)
        assert result is True
    
    def test_verify_hmac_signature_invalid(self, security_validator):
        """Test HMAC signature verification with invalid signature."""
        body = '{"vm_name": "test"}'
        timestamp = '1234567890'
        invalid_signature = 'invalid_signature_abc123'
        
        result = security_validator.verify_hmac_signature(body, timestamp, invalid_signature)
        assert result is False
    
    def test_verify_hmac_signature_missing_params(self, security_validator):
        """Test HMAC signature verification with missing parameters."""
        result = security_validator.verify_hmac_signature(None, None, None)
        assert result is False
    
    def test_verify_ip_allowed(self, security_validator):
        """Test IP verification with allowed IP."""
        result = security_validator.verify_ip('192.168.1.100')
        assert result is True
    
    def test_verify_ip_not_allowed(self, security_validator):
        """Test IP verification with disallowed IP."""
        result = security_validator.verify_ip('192.168.1.200')
        assert result is False
    
    def test_verify_ip_no_restriction(self, mock_env_vars_no_ip):
        """Test IP verification when no IP restriction is set."""
        config = Config()
        validator = SecurityValidator(config)
        
        # Should allow any IP when ALLOW_IP is empty
        assert validator.verify_ip('192.168.1.100') is True
        assert validator.verify_ip('10.0.0.1') is True
        assert validator.verify_ip('8.8.8.8') is True
    
    def test_verify_authentication_success(self, security_validator):
        """Test full authentication with valid credentials."""
        body = '{"vm_name": "test"}'
        timestamp = '1234567890'
        
        # Generate valid signature
        message = f"{body}{timestamp}"
        valid_signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Mock request
        request = Mock()
        request.client.host = '192.168.1.100'
        
        # Should not raise exception
        result = security_validator.verify_authentication(
            request=request,
            x_api_key='test_api_key_12345',
            x_signature=valid_signature,
            x_timestamp=timestamp,
            body=body
        )
        assert result is True
