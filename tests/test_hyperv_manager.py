"""
Tests for HyperVManager class
"""
import pytest
from unittest.mock import Mock, patch
from controller_api import HyperVManager


class TestHyperVManager:
    """Test suite for HyperVManager class."""
    
    @pytest.fixture
    def hyperv_manager(self):
        """Create HyperVManager instance for testing."""
        return HyperVManager()
    
    @patch('subprocess.run')
    def test_get_all_vm_names_success(self, mock_run, hyperv_manager, mock_hyperv_get_vm_success):
        """Test getting VM names with successful response."""
        mock_run.return_value = Mock(
            stdout=mock_hyperv_get_vm_success,
            returncode=0
        )
        
        result = hyperv_manager.get_all_vm_names()
        
        assert isinstance(result, list)
        assert 'VM-Test-01' in result
        assert len(result) == 1
    
    @patch('subprocess.run')
    def test_get_all_vm_names_empty(self, mock_run, hyperv_manager, mock_hyperv_empty):
        """Test getting VM names with empty response."""
        mock_run.return_value = Mock(
            stdout=mock_hyperv_empty,
            returncode=0
        )
        
        result = hyperv_manager.get_all_vm_names()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('subprocess.run')
    def test_get_all_vm_names_error(self, mock_run, hyperv_manager):
        """Test getting VM names with error response."""
        mock_run.return_value = Mock(
            stdout="",
            returncode=1
        )
        
        with pytest.raises(Exception):
            hyperv_manager.get_all_vm_names()
    
    @patch('subprocess.run')
    def test_validate_vm_exists_true(self, mock_run, hyperv_manager, sample_vm_names):
        """Test VM validation for existing VM."""
        with patch.object(hyperv_manager, 'get_all_vm_names', return_value=sample_vm_names):
            result = hyperv_manager.validate_vm_exists('VM-Test-01')
            assert result is True
    
    @patch('subprocess.run')
    def test_validate_vm_exists_false(self, mock_run, hyperv_manager, sample_vm_names):
        """Test VM validation for non-existing VM."""
        with patch.object(hyperv_manager, 'get_all_vm_names', return_value=sample_vm_names):
            result = hyperv_manager.validate_vm_exists('VM-NonExistent')
            assert result is False
    
    @patch('subprocess.run')
    def test_start_vm_success(self, mock_run, hyperv_manager):
        """Test starting VM successfully."""
        mock_run.return_value = Mock(
            stdout="VM started",
            returncode=0
        )
        
        result = hyperv_manager.start_vm('VM-Test-01')
        
        assert result is True
        mock_run.assert_called_once()
        # Verify PowerShell command contains Start-VM
        call_args = mock_run.call_args[0][0]
        assert 'Start-VM' in ' '.join(call_args)
    
    @patch('subprocess.run')
    def test_stop_vm_success(self, mock_run, hyperv_manager):
        """Test stopping VM successfully."""
        mock_run.return_value = Mock(
            stdout="VM stopped",
            returncode=0
        )
        
        result = hyperv_manager.stop_vm('VM-Test-01')
        
        assert result is True
        mock_run.assert_called_once()
        # Verify PowerShell command contains Stop-VM
        call_args = mock_run.call_args[0][0]
        assert 'Stop-VM' in ' '.join(call_args)
    
    @patch('subprocess.run')
    def test_restart_vm_success(self, mock_run, hyperv_manager):
        """Test restarting VM successfully."""
        mock_run.return_value = Mock(
            stdout="VM restarted",
            returncode=0
        )
        
        result = hyperv_manager.restart_vm('VM-Test-01')
        
        assert result is True
        mock_run.assert_called_once()
        # Verify PowerShell command contains Restart-VM
        call_args = mock_run.call_args[0][0]
        assert 'Restart-VM' in ' '.join(call_args)
    
    @patch('subprocess.run')
    def test_start_vm_failure(self, mock_run, hyperv_manager):
        """Test VM start failure."""
        mock_run.return_value = Mock(
            stdout="Error: VM not found",
            returncode=1
        )
        
        with pytest.raises(Exception):
            hyperv_manager.start_vm('VM-Test-01')
    
    @patch('subprocess.run')
    def test_stop_vm_failure(self, mock_run, hyperv_manager):
        """Test VM stop failure."""
        mock_run.return_value = Mock(
            stdout="Error: VM not found",
            returncode=1
        )
        
        with pytest.raises(Exception):
            hyperv_manager.stop_vm('VM-Test-01')
