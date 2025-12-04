# VM Controller API - Test Suite

Comprehensive test suite for the VM Controller API using pytest.

## 📋 Test Coverage

### Test Files

- **test_config.py** - Configuration loading and validation
- **test_security.py** - Authentication, HMAC, and IP verification
- **test_log_manager.py** - Audit and application logging
- **test_hyperv_manager.py** - Hyper-V VM operations (mocked)
- **test_middleware.py** - IP verification middleware
- **test_api_endpoints.py** - API endpoint responses

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
pytest tests/ --cov=. --cov-report=html

# View coverage report
start htmlcov/index.html
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
├── test_config.py              # Configuration tests
├── test_security.py            # Security validation tests
├── test_log_manager.py         # Logging tests
├── test_hyperv_manager.py      # Hyper-V operations tests (mocked)
├── test_middleware.py          # Middleware tests
├── test_api_endpoints.py       # API endpoint tests
└── README.md                   # This file
```

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

## 🎯 Coverage Goals

Target coverage by module:
- Config: 100%
- SecurityValidator: 95%+
- LogManager: 90%+
- HyperVManager: 85%+ (limited by PowerShell mocking)
- Middleware: 90%+
- API Endpoints: 80%+

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
