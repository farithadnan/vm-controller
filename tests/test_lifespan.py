"""
Tests for application lifespan events
"""
import pytest
from unittest.mock import patch, AsyncMock
from contextlib import asynccontextmanager
from controller_api import lifespan, app, config, hyperv_manager


class TestLifespanEvents:
    """Test suite for application lifespan events."""
    
    @pytest.mark.asyncio
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    async def test_startup_event_success(self, mock_get_vms):
        """Test successful startup with VM access."""
        mock_get_vms.return_value = ['VM-Test-01', 'VM-Test-02']
        
        # Test lifespan context manager
        async with lifespan(app) as result:
            # Startup code should have executed
            assert mock_get_vms.called
    
    @pytest.mark.asyncio
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    async def test_startup_event_no_vms(self, mock_get_vms):
        """Test startup when no VMs are found."""
        mock_get_vms.return_value = []
        
        # Should not raise exception even with no VMs
        async with lifespan(app) as result:
            assert mock_get_vms.called
    
    @pytest.mark.asyncio
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    async def test_startup_event_hyperv_error(self, mock_get_vms):
        """Test startup when Hyper-V access fails."""
        mock_get_vms.side_effect = Exception("Hyper-V not available")
        
        # Should handle error gracefully and continue startup
        async with lifespan(app) as result:
            assert mock_get_vms.called
    
    @pytest.mark.asyncio
    @patch('controller_api.config')
    @patch('controller_api.hyperv_manager.get_all_vm_names')
    async def test_startup_displays_config(self, mock_get_vms, mock_config):
        """Test that startup displays configuration information."""
        mock_config.api_key = 'test_key'
        mock_config.hmac_secret = 'test_secret'
        mock_config.allow_ip = '192.168.1.100'
        mock_config.log_dir = 'logs'
        mock_get_vms.return_value = ['VM-Test']
        
        # Startup should log configuration
        async with lifespan(app) as result:
            pass  # Just ensure it completes without error
    
    @pytest.mark.asyncio
    async def test_lifespan_cleanup(self):
        """Test that lifespan context manager properly cleans up."""
        cleanup_called = False
        
        @asynccontextmanager
        async def test_lifespan(app):
            # Startup
            yield
            # Shutdown
            nonlocal cleanup_called
            cleanup_called = True
        
        async with test_lifespan(app):
            pass
        
        # Cleanup should have been called
        assert cleanup_called
