# Contributing to ZeroMonitor

Thank you for your interest in contributing to ZeroMonitor! This document provides guidelines for code contributions.

## Code of Conduct

Please be respectful and professional in all interactions. We aim to maintain a welcoming and inclusive community.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv, virtualenv, or poetry)

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ZeroMonitor.git
   cd ZeroMonitor
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Setup environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your local/test settings
   ```

5. **Run tests to verify setup:**
   ```bash
   pytest
   pytest --cov=src  # With coverage report
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 standards
- Use 4 spaces for indentation
- Keep lines under 100 characters when practical
- Use meaningful variable and function names

### Type Hints

- Add type hints to all function signatures
- Use appropriate types from `typing` module
- Document complex types in docstrings

### Logging

- Use module-level logger: `logger = logging.getLogger(__name__)`
- Never use bare `print()` for logging
- Use appropriate log levels: `debug`, `info`, `warning`, `error`
- Include context information in log messages

### Security

⚠️ **CRITICAL:** Never commit credentials, API keys, or sensitive data.

**Credential Guidelines:**
- Use environment variables for all secrets
- Load from `.env` file (not committed to git)
- Document required credentials in `.env.example`
- Use `.gitignore` to protect sensitive files

```python
# ✅ CORRECT
password = os.getenv("DATABASE_PASSWORD")

# ❌ WRONG
password = "my_secret_password"
```

### Documentation

#### Module Docstrings
```python
"""
Brief module description.

More detailed explanation of what this module does and its role
in the system.
"""
```

#### Class Docstrings
```python
class MyClass:
    """
    Brief class description.

    Longer explanation including:
    - Responsibilities
    - Key attributes
    - Usage patterns
    """
```

#### Function Docstrings
```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of what function does.

    More detailed explanation if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong
    """
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_datainterpreter.py

# Run specific test
pytest tests/test_datainterpreter.py::test_function_name

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Writing Tests

- Create test files in `tests/` directory
- Name test files `test_*.py` or `*_test.py`
- Name test functions `test_*`
- Use descriptive test names: `test_should_return_error_when_invalid_input`
- Mock external dependencies
- Aim for 100% code coverage

```python
def test_metric_evaluation_warns_on_high_cpu():
    """Test that high CPU usage triggers warning severity."""
    interpreter = DataInterpreter(mock_bus, mock_config)
    result = interpreter._annotate_severity({"cpu_load": 0.95}, 0.80)
    assert result["cpu_load"]["severity"] == "warning"
```

### Coverage Requirements

- Target: **100% statement coverage**
- Run coverage report: `pytest --cov=src`
- View HTML report: `coverage html && open htmlcov/index.html`
- Minimum for PR: 95% coverage

## Commit Guidelines

### Commit Messages

Use clear, descriptive commit messages:

```
[TYPE] Brief description (max 50 chars)

More detailed explanation of changes if needed.
Explain WHAT and WHY, not HOW.

Fixes #123
```

### Commit Types
- `[FEATURE]` - New functionality
- `[BUGFIX]` - Bug fix
- `[REFACTOR]` - Code refactoring without behavior change
- `[DOCS]` - Documentation improvements
- `[TEST]` - Test additions or improvements
- `[SECURITY]` - Security improvements

### Example Commits
```
[SECURITY] Remove hardcoded credentials, use environment variables

Credentials are now loaded from environment variables or .env file.
Updated .env.example template for setup documentation.

Fixes #456

[FEATURE] Add email alert notifications for metric warnings

Implement SMTP integration to send alerts when metrics exceed thresholds.
Configuration via environment variables for flexible deployment.

[TEST] Add 100% coverage for DataInterpreter module

Add tests for edge cases in threshold evaluation and severity calculation.
```

## Pull Request Process

1. **Before starting:** Check for open issues or PRs addressing the same problem

2. **Create feature branch:**
   ```bash
   git checkout -b feature/brief-description
   ```

3. **Make your changes:**
   - Keep commits focused and logical
   - Write descriptive commit messages
   - Update documentation as needed

4. **Run tests locally:**
   ```bash
   pytest --cov=src
   ```

5. **Verify no credentials exposed:**
   ```bash
   git diff HEAD~1  # Review what you're committing
   grep -r "password\|api_key\|secret" src/  # Search for secrets
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/brief-description
   ```

7. **Open Pull Request:**
   - Write clear PR description
   - Link related issues
   - Describe testing performed
   - Note any breaking changes

8. **PR Requirements:**
   - ✅ Tests pass locally
   - ✅ Coverage >= 95%
   - ✅ No hardcoded credentials
   - ✅ Code follows style guidelines
   - ✅ Documentation updated
   - ✅ Commits are clean and descriptive

## Architecture Overview

### Module Structure
```
src/
  ├── main.py              # Entry point
  ├── event_bus.py         # Event distribution system
  ├── driver.py            # Polling agent coordinator
  ├── polling_agent.py     # Remote metrics collection
  ├── datainterpreter.py   # Metrics processing & analysis
  ├── security_manager.py  # Vault & encryption
  ├── network_manager.py   # Network configuration
  ├── paths.py            # Path management
  └── constants.py        # Configuration constants

ui/
  ├── display_ui.py       # Main UI controller
  ├── control_ui.py       # UI event publishing
  ├── theme.py            # Styling & colors
  ├── utilities.py        # UI helpers
  └── screens/            # Screen implementations
  └── widgets/            # Reusable UI components

Pairing/
  ├── pairing_control.py  # Device pairing logic
  ├── endpoint.py         # Pairing endpoint
  └── transfer.py         # Secure file transfer

tests/
  ├── test_*.py          # Test files
  └── conftest.py        # Pytest fixtures
```

### Key Data Flows

1. **Metrics Collection:**
   - PollingAgent → MetricEvent → EventBus → DataInterpreter → cache_data.json

2. **Alerts:**
   - DataInterpreter → EventBus → Email/UI notifications

3. **Configuration:**
   - Environment variables → Config object → All modules

## Common Issues & Solutions

### Import Errors
- Ensure you're in virtual environment: `which python` should show `.venv`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check PYTHONPATH: `echo $PYTHONPATH`

### Test Failures
- Clear cache: `rm -rf .pytest_cache __pycache__`
- Rebuild environment: `pip install -r requirements.txt`
- Check for uncommitted `.env` changes

### Credential Leaks
- Never commit `.env` file (protected by `.gitignore`)
- Check git history: `git log -p | grep -i password`
- Rotate credentials if exposed
- Use `.env.example` template for documentation

## Resources

- **Python Style Guide:** [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **Type Hints:** [PEP 484](https://www.python.org/dev/peps/pep-0484/)
- **Documentation:** [PEP 257](https://www.python.org/dev/peps/pep-0257/)
- **Pytest Guide:** [pytest documentation](https://docs.pytest.org/)
- **Logging:** [Python logging docs](https://docs.python.org/3/library/logging.html)

## Questions?

- Check existing issues and PRs
- Review REFACTORING_SUMMARY.md for recent changes
- Open a GitHub discussion
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as this project.

---

Thank you for contributing to ZeroMonitor! 🎉

