"""
Tests for SecurityValidator class - CORRECTED to match actual API
"""
import hmac
import hashlib
import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from controller_api import Config, SecurityValidator


class TestSecurityValidator:
    """Test suite for SecurityValidator class."""
    
    @pytest.fixture
    def security_validator(self, mock_env_vars):
        """Create SecurityValidator instance for testing."""
        config = Config()
        return SecurityValidator(config)
    
    def test_verify_api_key_valid(self, security_validator):
        """Test API key verification with valid key - should not raise exception."""
        # verify_api_key raises exception on failure, returns None on success
        try:
            security_validator.verify_api_key('test_api_key_12345')
            assert True  # Passed if no exception
        except HTTPException:
            pytest.fail("Should not raise exception for valid API key")
    
    def test_verify_api_key_invalid(self, security_validator):
        """Test API key verification with invalid key - should raise exception."""
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_api_key('wrong_key')
        assert exc_info.value.status_code == 401
    
    def test_verify_api_key_none(self, security_validator):
        """Test API key verification with None - should raise exception."""
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_api_key(None)
        assert exc_info.value.status_code == 401
    
    def test_verify_api_key_empty(self, security_validator):
        """Test API key verification with empty string - should raise exception."""
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_api_key('')
        assert exc_info.value.status_code == 401
    
    def test_verify_hmac_signature_valid(self, security_validator):
        """Test HMAC signature verification with valid signature."""
        body = b'{"vm_name": "test"}'  # bytes!
        timestamp = '1234567890'
        
        # Generate valid signature
        message = body + timestamp.encode()
        valid_signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Should not raise exception
        try:
            security_validator.verify_hmac_signature(valid_signature, timestamp, body)
            assert True
        except HTTPException:
            pytest.fail("Should not raise exception for valid signature")
    
    def test_verify_hmac_signature_invalid(self, security_validator):
        """Test HMAC signature verification with invalid signature."""
        body = b'{"vm_name": "test"}'
        timestamp = '1234567890'
        invalid_signature = 'invalid_signature_abc123'
        
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_hmac_signature(invalid_signature, timestamp, body)
        assert exc_info.value.status_code == 401
    
    def test_verify_hmac_signature_missing_params(self, security_validator):
        """Test HMAC signature verification with missing parameters."""
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_hmac_signature(None, None, b'')
        assert exc_info.value.status_code == 401
    
    def test_verify_ip_allowed(self, security_validator):
        """Test IP verification with allowed IP."""
        try:
            security_validator.verify_ip('192.168.1.100')
            assert True
        except HTTPException:
            pytest.fail("Should not raise exception for allowed IP")
    
    def test_verify_ip_not_allowed(self, security_validator):
        """Test IP verification with disallowed IP."""
        with pytest.raises(HTTPException) as exc_info:
            security_validator.verify_ip('192.168.1.200')
        assert exc_info.value.status_code == 403
    
    def test_verify_ip_no_restriction(self, mock_env_vars_no_ip):
        """Test IP verification when no IP restriction is set."""
        config = Config()
        validator = SecurityValidator(config)
        
        # Should allow any IP
        try:
            validator.verify_ip('192.168.1.100')
            validator.verify_ip('10.0.0.1')
            assert True
        except HTTPException:
            pytest.fail("Should not raise exception when IP restriction disabled")
    
    @pytest.mark.asyncio
    async def test_verify_authentication_success(self, security_validator):
        """Test full authentication."""
        from unittest.mock import AsyncMock
        
        body_bytes = b'test body'
        timestamp = '1234567890'
        
        message = body_bytes + timestamp.encode()
        valid_signature = hmac.new(
            'test_hmac_secret_67890'.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        request = Mock()
        request.client.host = '192.168.1.100'
        request.body = AsyncMock(return_value=body_bytes)  # Use AsyncMock for async method
        
        try:
            result = await security_validator.verify_authentication(
                request=request,
                x_api_key='test_api_key_12345',
                x_signature=valid_signature,
                x_timestamp=timestamp
            )
            assert result is True
        except HTTPException:
            pytest.fail("Should not raise exception")
