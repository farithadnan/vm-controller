"""
Tests for API endpoints - CORRECTED (accounts for middleware IP blocking)
"""
import hmac
import hashlib
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from controller_api import app, config


# Note: TestClient triggers middleware which blocks IPs
# We need to mock/disable IP verification for these tests

class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @patch('controller_api.security_validator.verify_ip')
    def test_root_endpoint(self, mock_verify_ip):
        """Test root endpoint returns basic info."""
        mock_verify_ip.return_value = True  # Allow all IPs for test
        
        client = TestClient(app)
        response = client.get("/")
        
        # Response might be 200 or contain data
        assert response.status_code == 200
        data = response.json()
        # Check that response has expected structure
        assert 'message' in data or 'status' in data or 'version' in data
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    def test_health_check_healthy(self, mock_get_vms, mock_verify_ip):
        """Test health check endpoint when service is healthy."""
        mock_verify_ip.return_value = True
        mock_get_vms.return_value = ['VM-Test-01', 'VM-Test-02']
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['vm_count'] == 2
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    def test_health_check_unhealthy(self, mock_get_vms, mock_verify_ip):
        """Test health check when Hyper-V service is unavailable."""
        mock_verify_ip.return_value = True
        mock_get_vms.side_effect = Exception("Hyper-V service unavailable")
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 503
        assert 'Service unhealthy' in response.json()['detail']


class TestAuthenticatedEndpoints:
    """Test suite for authenticated endpoints."""
    
    def _create_auth_headers(self, body=b""):
        """Helper to create valid authentication headers."""
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        message = body + timestamp.encode()
        signature = hmac.new(
            config.hmac_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return {
            'x-api-key': config.api_key,
            'x-signature': signature,
            'x-timestamp': timestamp
        }
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    def test_list_vms_success(self, mock_get_vms, mock_verify_ip):
        """Test list VMs endpoint with valid authentication."""
        mock_verify_ip.return_value = True
        mock_get_vms.return_value = ['VM-Test-01', 'VM-Test-02', 'VM-Production']
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.get("/vm/list", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert 'vms' in data
        assert len(data['vms']) == 3
        assert 'VM-Test-01' in data['vms']
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    def test_list_vms_empty(self, mock_get_vms, mock_verify_ip):
        """Test list VMs when no VMs exist."""
        mock_verify_ip.return_value = True
        mock_get_vms.return_value = []
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.get("/vm/list", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data['vms'] == []
        assert 'count' not in data  # API doesn't return count field
    
    @patch('controller_api.security_validator.verify_ip')
    def test_list_vms_no_auth(self, mock_verify_ip):
        """Test list VMs without authentication headers."""
        mock_verify_ip.return_value = True
        
        client = TestClient(app)
        response = client.get("/vm/list")
        
        # Should fail due to missing authentication
        assert response.status_code in [401, 422]
    
    @patch('controller_api.security_validator.verify_ip')
    def test_list_vms_invalid_api_key(self, mock_verify_ip):
        """Test list VMs with invalid API key."""
        mock_verify_ip.return_value = True
        
        headers = self._create_auth_headers()
        headers['x-api-key'] = 'invalid_key_12345'
        
        client = TestClient(app)
        response = client.get("/vm/list", headers=headers)
        
        assert response.status_code == 401
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.validate_vm_exists')
    @patch('controller_api.hyperv_manager.start_vm')
    def test_start_vm_success(self, mock_start, mock_validate, mock_verify_ip):
        """Test starting a VM successfully."""
        mock_verify_ip.return_value = True
        mock_validate.return_value = True
        mock_start.return_value = "VM started successfully"
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.post("/vm/test-vm/start", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['vm'] == 'test-vm'
        assert data['action'] == 'start'
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.validate_vm_exists')
    def test_start_vm_not_found(self, mock_validate, mock_verify_ip):
        """Test starting a non-existent VM."""
        mock_verify_ip.return_value = True
        from fastapi import HTTPException
        mock_validate.side_effect = HTTPException(status_code=404, detail="VM not found")
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.post("/vm/nonexistent/start", headers=headers)
        
        assert response.status_code == 404
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.validate_vm_exists')
    @patch('controller_api.hyperv_manager.stop_vm')
    def test_stop_vm_success(self, mock_stop, mock_validate, mock_verify_ip):
        """Test stopping a VM successfully."""
        mock_verify_ip.return_value = True
        mock_validate.return_value = True
        mock_stop.return_value = "VM stopped successfully"
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.post("/vm/test-vm/shutdown", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['action'] == 'shutdown'
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.validate_vm_exists')
    @patch('controller_api.hyperv_manager.stop_vm')
    def test_stop_vm_error(self, mock_stop, mock_validate, mock_verify_ip):
        """Test VM stop failure."""
        mock_verify_ip.return_value = True
        mock_validate.return_value = True
        mock_stop.side_effect = Exception("Failed to stop VM")
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.post("/vm/test-vm/shutdown", headers=headers)
        
        assert response.status_code == 500
        assert 'Failed to' in response.json()['detail']
    
    @patch('controller_api.security_validator.verify_ip')
    @patch('controller_api.hyperv_manager.validate_vm_exists')
    @patch('controller_api.hyperv_manager.restart_vm')
    def test_restart_vm_success(self, mock_restart, mock_validate, mock_verify_ip):
        """Test restarting a VM successfully."""
        mock_verify_ip.return_value = True
        mock_validate.return_value = True
        mock_restart.return_value = "VM restarted successfully"
        
        client = TestClient(app)
        headers = self._create_auth_headers()
        response = client.post("/vm/test-vm/restart", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['action'] == 'restart'
