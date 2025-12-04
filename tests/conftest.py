"""
Pytest configuration and shared fixtures
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'API_KEY': 'test_api_key_12345',
        'HMAC_SECRET': 'test_hmac_secret_67890',
        'ALLOW_IP': '192.168.1.100'
    }):
        yield


@pytest.fixture
def mock_env_vars_no_ip():
    """Mock environment variables without IP restriction."""
    with patch.dict(os.environ, {
        'API_KEY': 'test_api_key_12345',
        'HMAC_SECRET': 'test_hmac_secret_67890',
        'ALLOW_IP': ''
    }):
        yield


@pytest.fixture
def sample_vm_names():
    """Sample VM names for testing."""
    return ['VM-Test-01', 'VM-Test-02', 'VM-Production']


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object."""
    request = Mock()
    request.client.host = '192.168.1.100'
    request.method = 'GET'
    request.url.path = '/test'
    return request


@pytest.fixture
def mock_hyperv_get_vm_success():
    """Mock successful Hyper-V Get-VM command."""
    return "Name               State   CPUUsage(%) MemoryAssigned(M) Uptime\nVM-Test-01         Running 0           1024              00:30:00"


@pytest.fixture
def mock_hyperv_empty():
    """Mock empty Hyper-V response (no VMs)."""
    return ""
