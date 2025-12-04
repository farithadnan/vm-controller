"""
Tests for IPVerificationMiddleware
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from controller_api import Config, LogManager, SecurityValidator, IPVerificationMiddleware


class TestIPVerificationMiddleware:
    """Test suite for IPVerificationMiddleware."""
    
    @pytest.fixture
    def middleware_components(self, mock_env_vars):
        """Create middleware components for testing."""
        config = Config()
        log_manager = LogManager(config)
        security_validator = SecurityValidator(config)
        return log_manager, security_validator
    
    @pytest.mark.asyncio
    async def test_middleware_allows_valid_ip(self, middleware_components, mock_request):
        """Test that middleware allows requests from valid IP."""
        log_manager, security_validator = middleware_components
        
        middleware = IPVerificationMiddleware(
            app=Mock(),
            log_manager=log_manager,
            security_validator=security_validator
        )
        
        # Mock the call_next function
        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            return response
        
        # Should not raise exception for allowed IP
        with patch.object(log_manager, 'log_request_entry'):
            response = await middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_invalid_ip(self, middleware_components):
        """Test that middleware blocks requests from invalid IP."""
        log_manager, security_validator = middleware_components
        
        middleware = IPVerificationMiddleware(
            app=Mock(),
            log_manager=log_manager,
            security_validator=security_validator
        )
        
        # Create request with disallowed IP
        request = Mock()
        request.client.host = '192.168.1.200'  # Not allowed
        request.method = 'GET'
        request.url.path = '/test'
        
        async def mock_call_next(request):
            response = Mock()
            return response
        
        # Should raise HTTPException for blocked IP
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_call_next)
        
        assert exc_info.value.status_code == 403
        assert "IP address not allowed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_middleware_logs_all_requests(self, middleware_components, mock_request):
        """Test that middleware logs all requests."""
        log_manager, security_validator = middleware_components
        
        middleware = IPVerificationMiddleware(
            app=Mock(),
            log_manager=log_manager,
            security_validator=security_validator
        )
        
        async def mock_call_next(request):
            response = Mock()
            response.status_code = 200
            return response
        
        # Mock log_request_entry to verify it's called
        with patch.object(log_manager, 'log_request_entry') as mock_log:
            await middleware.dispatch(mock_request, mock_call_next)
            mock_log.assert_called_once()
