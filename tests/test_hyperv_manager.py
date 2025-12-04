"""
Tests for HyperVManager class - CORRECTED
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from controller_api import HyperVManager


class TestHyperVManager:
    """Test suite for HyperVManager class."""
    
    @pytest.fixture
    def hyperv_manager(self):
        """Create HyperVManager instance for testing."""
        return HyperVManager()
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_get_all_vm_names_success(self, mock_run, hyperv_manager):
        """Test getting VM names with successful response."""
        mock_run.return_value = "VM-Test-01\nVM-Test-02\nVM-Production"
        
        result = hyperv_manager.get_all_vm_names()
        
        assert isinstance(result, list)
        assert 'VM-Test-01' in result
        assert 'VM-Test-02' in result
        assert len(result) == 3
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_get_all_vm_names_empty(self, mock_run, hyperv_manager):
        """Test getting VM names with empty response."""
        mock_run.return_value = ""
        
        result = hyperv_manager.get_all_vm_names()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_validate_vm_exists_true(self, mock_run, hyperv_manager):
        """Test VM validation for existing VM."""
        mock_run.return_value = "VM-Test-01\nVM-Test-02"
        
        # Should not raise exception
        try:
            hyperv_manager.validate_vm_exists('VM-Test-01')
            assert True
        except HTTPException:
            pytest.fail("Should not raise exception for existing VM")
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_validate_vm_exists_false(self, mock_run, hyperv_manager):
        """Test VM validation for non-existing VM."""
        mock_run.return_value = "VM-Test-01\nVM-Test-02"
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            hyperv_manager.validate_vm_exists('VM-NonExistent')
        assert exc_info.value.status_code == 404
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_start_vm_success(self, mock_run, hyperv_manager):
        """Test starting VM successfully."""
        mock_run.return_value = "Success"
        
        result = hyperv_manager.start_vm('VM-Test-01')
        
        # Returns the output string
        assert result == "Success"
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_stop_vm_success(self, mock_run, hyperv_manager):
        """Test stopping VM successfully."""
        mock_run.return_value = "Success"
        
        result = hyperv_manager.stop_vm('VM-Test-01')
        
        assert result == "Success"
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_restart_vm_success(self, mock_run, hyperv_manager):
        """Test restarting VM successfully."""
        mock_run.return_value = "Success"
        
        result = hyperv_manager.restart_vm('VM-Test-01')
        
        assert result == "Success"
    
    @patch('subprocess.run')
    def test_run_powershell_error(self, mock_run, hyperv_manager):
        """Test PowerShell execution returns stderr on error."""
        mock_run.return_value = Mock(
            stdout="",
            stderr="Access denied",
            returncode=1
        )
        
        # _run_powershell returns stderr, doesn't raise exception
        result = hyperv_manager._run_powershell("Get-VM")
        assert result == "Access denied"
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_get_all_vm_names_with_spaces(self, mock_run, hyperv_manager):
        """Test getting VM names that contain spaces."""
        mock_run.return_value = "VM Test 01\nVM-Production\nTest Server 2023"
        
        result = hyperv_manager.get_all_vm_names()
        
        assert len(result) == 3
        assert 'VM Test 01' in result
        assert 'Test Server 2023' in result
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_validate_vm_exists_with_special_chars(self, mock_run, hyperv_manager):
        """Test VM validation with special characters in name."""
        mock_run.return_value = "VM-Test_01\nVM.Production\nVM (Backup)"
        
        # Should not raise exception for VM with parentheses
        try:
            hyperv_manager.validate_vm_exists('VM (Backup)')
            assert True
        except HTTPException:
            pytest.fail("Should handle special characters in VM names")
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_start_vm_already_running(self, mock_run, hyperv_manager):
        """Test starting a VM that's already running."""
        # PowerShell might return specific message for already running VM
        mock_run.return_value = "VM is already in Running state"
        
        result = hyperv_manager.start_vm('VM-Test-01')
        
        assert result is not None
    
    @patch('controller_api.HyperVManager._run_powershell')
    def test_stop_vm_already_stopped(self, mock_run, hyperv_manager):
        """Test stopping a VM that's already stopped."""
        mock_run.return_value = "VM is already in Off state"
        
        result = hyperv_manager.stop_vm('VM-Test-01')
        
        assert result is not None
