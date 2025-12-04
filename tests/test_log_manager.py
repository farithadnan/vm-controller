"""
Tests for LogManager class
"""
import os
import json
import pytest
from unittest.mock import Mock, patch, mock_open
from controller_api import Config, LogManager


class TestLogManager:
    """Test suite for LogManager class."""
    
    @pytest.fixture
    def log_manager(self, mock_env_vars):
        """Create LogManager instance for testing."""
        config = Config()
        return LogManager(config)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_audit_creates_log_entry(self, mock_file, log_manager):
        """Test that write_audit creates properly formatted log entry."""
        log_manager.write_audit(
            action="start",
            vm="test-vm",
            ip="192.168.1.100",
            status="success",
            details="VM started successfully"
        )
        
        # Verify file was opened in append mode
        mock_file.assert_called_once()
        
        # Get what was written
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Parse JSON and verify contents
        log_entry = json.loads(written_data)
        assert log_entry['action'] == 'start'
        assert log_entry['vm'] == 'test-vm'
        assert log_entry['client_ip'] == '192.168.1.100'
        assert log_entry['status'] == 'success'
        assert log_entry['details'] == 'VM started successfully'
        assert 'timestamp' in log_entry
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_app_log_creates_log_entry(self, mock_file, log_manager):
        """Test that write_app_log creates properly formatted log entry."""
        log_data = {
            "event": "api_request",
            "path": "/vm/list",
            "status": "success"
        }
        
        log_manager.write_app_log(log_data)
        
        # Verify file was opened
        mock_file.assert_called_once()
        
        # Get what was written
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Parse JSON and verify contents
        log_entry = json.loads(written_data)
        assert log_entry['event'] == 'api_request'
        assert log_entry['path'] == '/vm/list'
        assert log_entry['status'] == 'success'
        assert 'timestamp' in log_entry
    
    @patch('builtins.open', new_callable=mock_open)
    def test_log_request_entry(self, mock_file, log_manager, mock_request):
        """Test that log_request_entry logs request details."""
        log_manager.log_request_entry(
            request=mock_request,
            status="received",
            details="Request received"
        )
        
        # Verify file was opened
        mock_file.assert_called_once()
        
        # Get what was written
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        
        # Parse JSON and verify contents
        log_entry = json.loads(written_data)
        assert log_entry['method'] == 'GET'
        assert log_entry['path'] == '/test'
        assert log_entry['client_ip'] == '192.168.1.100'
        assert log_entry['status'] == 'received'
        assert 'timestamp' in log_entry
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_write_audit_handles_io_error(self, mock_file, log_manager):
        """Test that write_audit handles IO errors gracefully."""
        # Should not raise exception
        log_manager.write_audit(
            action="start",
            vm="test-vm",
            ip="192.168.1.100",
            status="success"
        )
