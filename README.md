# ZeroMonitor  
**Agent-less Hardware Monitoring System**  
*ERAU Capstone Project*

---

## Overview  
ZeroMonitor is a lightweight, agent-less hardware monitoring system designed to collect and display system metrics without requiring software installation on target machines.  

The project focuses on delivering a **scalable, low-overhead solution** for monitoring system health across multiple devices in real time.

Unlike traditional monitoring tools that rely on installed agents, ZeroMonitor uses **network-based data collection**, reducing system impact and simplifying deployment.

---

## Quick Start

### Prerequisites
- Python 3.11+
- SSH access to target systems

### Installation

```bash
# Clone repository
git clone https://github.com/NP434/ZeroMonitor.git
cd ZeroMonitor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
nano .env  # Edit with your SMTP credentials (optional)

# Run tests
pytest

# Start the system
python -m src.main --dev  # Development mode
python -m src.main        # Production mode
```

---

## Features  
- 🛰️ Agent-less monitoring (no installation required on client machines)  
- ⚡ Real-time system metrics collection  
- 🪶 Lightweight and low resource usage  
- 🌐 Cross-platform compatibility  
- 📈 Scalable architecture for multiple devices  
- 🎨 Clean and intuitive data visualization interface  
- 📧 Email alerts for metric thresholds (optional)
- 🔒 Encrypted credential storage
- 🔐 SSH key-based authentication

---

## Architecture  

ZeroMonitor follows a **client-server model**:

### 🔹 Target Systems  
- No installed agents  
- Expose hardware/system data through accessible interfaces  

### 🔹 Backend
- Collects and processes system data via SSH  
- Normalizes and stores metrics in JSON cache  
- Evaluates thresholds and generates alerts

### 🔹 Frontend Interface  
- Displays real-time hardware data  
- Provides a user-friendly dashboard  
- Real-time metric visualization

---

## Metrics Collected  
- **CPU:** Load average, temperature, clock speed, core voltage
- **Memory:** Total, used, percentage utilization
- **Disk:** Usage percentage
- **Network:** RX/TX bandwidth
- **System:** Uptime

---

## Project Goals  
- Eliminate the need for intrusive monitoring agents  
- Provide a simple deployment model  
- Enable real-time visibility into system performance  
- Build a scalable monitoring solution for enterprise environments  

---

## Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guidelines for contributing
- **[SECURITY.md](SECURITY.md)** - Security policies and best practices
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Recent code cleanup details
- **[class structure.txt](class structure.txt)** - System architecture overview

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Optional: Email alerts for metric warnings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=alert-recipient@example.com
SEND_ALERTS=true
```

### Development Mode

Run with development configuration:
```bash
python -m src.main --dev
```

This uses local `dev_vault/` directory instead of system paths.

---

## Development

### Running Tests
```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src

# Specific test file
pytest tests/test_datainterpreter.py -v
```

### Code Style
- Follows PEP 8
- Type hints required
- 100% test coverage target

### Logging
- Development: console + file output
- Log file: `logs/system.log`

---

## Directory Structure

```
ZeroMonitor/
├── src/                 # Core modules
│   ├── main.py         # Entry point
│   ├── driver.py       # Polling coordinator
│   ├── polling_agent.py    # Remote metric collection
│   ├── datainterpreter.py  # Metric processing
│   ├── event_bus.py    # Event distribution
│   ├── constants.py    # Configuration constants
│   └── ...
├── ui/                 # Pygame UI
│   ├── display_ui.py   # Main UI controller
│   ├── screens/        # Screen implementations
│   └── widgets/        # UI components
├── tests/              # Test suite
├── data/              # Runtime data
├── logs/              # System logs
└── Pairing/           # Device pairing module
```

---

## Performance

- **Polling Interval:** Configurable (default 10 seconds)
- **Memory Footprint:** ~50-100 MB
- **CPU Usage:** <5% (typical)
- **Supported Devices:** 50+ concurrent nodes
- **Cache File:** Single JSON file per device

---

## Troubleshooting

### SSH Connection Issues
- Verify SSH key permissions: `chmod 600 ~/.ssh/id_ed25519`
- Test connection: `ssh user@host "uname -a"`
- Check firewall rules allow port 22

### Email Alerts Not Working
- Verify SMTP credentials in `.env`
- Check firewall allows outbound SMTP (port 465)
- Enable "Less secure app access" for Gmail
- Set `SEND_ALERTS=true` in `.env`

### Tests Failing
- Clear cache: `rm -rf .pytest_cache`
- Reinstall deps: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.11+)

---

## Contributors

- See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute
- Project contributors listed in git commit history

---

## License

[Your License Here]

---

## Status Badges

[![Run Pytest](https://github.com/NP434/ZeroMonitor/actions/workflows/tests.yml/badge.svg)](https://github.com/NP434/ZeroMonitor/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)]()

---

## Questions?

- Check the documentation files
- Review existing issues
- Create a new issue with details
- See [SECURITY.md](SECURITY.md) for security issues (private disclosure)
