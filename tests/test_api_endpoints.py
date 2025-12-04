"""
Tests for API endpoints - CORRECTED (accounts for middleware IP blocking)
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from controller_api import app


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
