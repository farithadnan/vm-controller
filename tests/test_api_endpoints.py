"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from controller_api import app, config, hyperv_manager


# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'VM Controller API is running'
        assert 'version' in data
        assert 'timestamp' in data
    
    @patch.object(hyperv_manager, 'get_all_vm_names')
    def test_health_check_healthy(self, mock_get_vms):
        """Test health check endpoint when service is healthy."""
        mock_get_vms.return_value = ['VM-Test-01', 'VM-Test-02']
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['vm_count'] == 2
        assert 'timestamp' in data
    
    @patch.object(hyperv_manager, 'get_all_vm_names')
    def test_health_check_unhealthy(self, mock_get_vms):
        """Test health check endpoint when service is unhealthy."""
        mock_get_vms.side_effect = Exception("Hyper-V service unavailable")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        assert 'Service unhealthy' in response.json()['detail']


class TestAuthenticatedEndpoints:
    """Test suite for authenticated endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for testing."""
        import hmac
        import hashlib
        from datetime import datetime, timezone
        
        body = ""
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        message = f"{body}{timestamp}"
        signature = hmac.new(
            config.hmac_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'x-api-key': config.api_key,
            'x-signature': signature,
            'x-timestamp': timestamp
        }
    
    @patch.object(hyperv_manager, 'get_all_vm_names')
    def test_list_vms_authenticated(self, mock_get_vms, auth_headers):
        """Test list VMs endpoint with authentication."""
        mock_get_vms.return_value = ['VM-Test-01', 'VM-Test-02']
        
        response = client.get("/vm/list", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert 'vms' in data
        assert len(data['vms']) == 2
    
    def test_list_vms_no_auth(self):
        """Test list VMs endpoint without authentication."""
        response = client.get("/vm/list")
        
        # Should fail authentication
        assert response.status_code in [401, 403, 422]
    
    def test_list_vms_invalid_api_key(self, auth_headers):
        """Test list VMs endpoint with invalid API key."""
        headers = auth_headers.copy()
        headers['x-api-key'] = 'invalid_key'
        
        response = client.get("/vm/list", headers=headers)
        
        assert response.status_code in [401, 403]
