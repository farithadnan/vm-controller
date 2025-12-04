# VM Controller API - Test Suite

Comprehensive test suite for the VM Controller API using pytest.

## 📋 Test Coverage

### Test Files

- **test_config.py** (6 tests) - Configuration loading and validation
- **test_security.py** (11 tests) - Authentication, HMAC, and IP verification
- **test_log_manager.py** (3 tests) - Audit and application logging
- **test_hyperv_manager.py** (13 tests) - Hyper-V VM operations (mocked)
- **test_middleware.py** (2 tests) - IP verification middleware
- **test_api_endpoints.py** (12 tests) - API endpoint responses
- **test_lifespan.py** (5 tests) - Application startup/shutdown events
- **test_edge_cases.py** (18 tests) - Edge cases and error scenarios

## 🚀 Running Tests

### Prerequisites

Install test dependencies:
```powershell
pip install pytest pytest-asyncio pytest-cov httpx
```

### Run All Tests

```powershell
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_security.py

# Run specific test
pytest tests/test_security.py::TestSecurityValidator::test_verify_api_key_valid
```

### With Coverage

```powershell
# Run tests with coverage report
pytest tests/ --cov=controller_api --cov-report=term-missing --cov-report=html

# View detailed HTML coverage report
start htmlcov/index.html

# Current coverage: 92% (203 statements, 17 missed)
```

### Watch Mode

```powershell
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw tests/
```

## 📊 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_config.py              # Configuration tests (6 tests)
├── test_security.py            # Security validation tests (11 tests)
├── test_log_manager.py         # Logging tests (3 tests)
├── test_hyperv_manager.py      # Hyper-V operations tests (13 tests)
├── test_middleware.py          # Middleware tests (2 tests)
├── test_api_endpoints.py       # API endpoint tests (12 tests)
├── test_lifespan.py            # Lifespan event tests (5 tests)
├── test_edge_cases.py          # Edge case tests (18 tests)
└── README.md                   # This file
```

### Test Categories

**test_config.py** - Configuration validation
- Environment variable loading
- Log directory creation
- Missing/empty credentials handling
- Windows path compatibility

**test_security.py** - Security mechanisms
- API key validation (valid, invalid, none, empty)
- HMAC-SHA256 signature verification
- IP whitelisting logic
- Full authentication flow

**test_log_manager.py** - Logging functionality
- Audit log creation (VM operations)
- Application log creation (all requests)
- Request entry logging with timestamps

**test_hyperv_manager.py** - VM operations
- Get all VM names (success, empty, with spaces)
- Validate VM exists (true/false, special characters)
- Start/Stop/Restart VMs (success, already running/stopped)
- PowerShell execution and error handling

**test_middleware.py** - Request processing
- IP verification allow/block
- Request logging at entry point

**test_api_endpoints.py** - HTTP endpoints
- Root endpoint and health check
- List VMs (success, empty, authentication failures)
- Start/Stop/Restart VMs (success, not found, errors)
- Authentication header validation

**test_lifespan.py** - Application lifecycle
- Startup event with VM access verification
- Startup with no VMs or errors
- Configuration display on startup
- Cleanup on shutdown

**test_edge_cases.py** - Edge cases and error scenarios
- Config: Empty credentials, nested directories
- LogManager: Unicode handling, empty details, existing timestamps
- Security: Whitespace in keys, IPv6 addresses, expired timestamps, empty bodies
- HyperV: Blank lines, whitespace, case sensitivity, timeouts, quotes in VM names

## 🧪 Test Fixtures

Common fixtures available in `conftest.py`:

- `mock_env_vars` - Mock environment variables with IP restriction
- `mock_env_vars_no_ip` - Mock environment variables without IP restriction
- `sample_vm_names` - Sample VM names for testing
- `mock_request` - Mock FastAPI Request object
- `mock_hyperv_get_vm_success` - Mock successful Hyper-V response
- `mock_hyperv_empty` - Mock empty Hyper-V response

## ✅ Test Categories

### Unit Tests
- Configuration loading and validation
- Security validation logic
- Logging functionality
- VM name parsing and validation

### Integration Tests
- Middleware behavior
- API endpoint responses
- Authentication flow

### Mocked Tests
- Hyper-V PowerShell commands (mocked to avoid requiring actual Hyper-V)
- File system operations
- Network requests

## 📝 Writing New Tests

Example test structure:

```python
import pytest
from unittest.mock import patch, Mock
from controller_api import YourClass

class TestYourClass:
    """Test suite for YourClass."""
    
    @pytest.fixture
    def your_fixture(self):
        """Create test fixture."""
        return YourClass()
    
    def test_your_function(self, your_fixture):
        """Test description."""
        result = your_fixture.your_method()
        assert result == expected_value
    
    @patch('module.function')
    def test_with_mock(self, mock_function, your_fixture):
        """Test with mocked dependencies."""
        mock_function.return_value = 'mocked_value'
        result = your_fixture.your_method()
        assert result == 'expected_result'
```

## 🎯 Coverage Status

**Overall: 92% coverage** (203 statements, 17 missed)

Achieved coverage by component:
- ✅ Config: ~95%
- ✅ SecurityValidator: ~95%
- ✅ LogManager: ~90%
- ✅ HyperVManager: ~90%
- ✅ Middleware: ~95%
- ✅ API Endpoints: ~90%

**Uncovered lines (8%):** Mostly error paths and edge cases:
- Error handling in Config initialization
- Rare PowerShell execution errors
- Specific error responses in API endpoints
- Some exception handling branches

## 🐛 Debugging Tests

```powershell
# Run with print statements visible
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Show local variables on failure
pytest tests/ -l
```

## 📚 References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)

## ⚠️ Important Notes

1. **Hyper-V commands are mocked** - Tests don't require actual Hyper-V installation
2. **Environment variables are mocked** - Tests use test values, not your actual `.env`
3. **File operations are mocked** - Tests don't write to actual log files
4. **Network requests are mocked** - Tests don't make real API calls

## 🔄 Continuous Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov httpx
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```
