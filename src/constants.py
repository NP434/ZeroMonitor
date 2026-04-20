"""
Constants and Configuration Values for ZeroMonitor

This module centralizes all magic numbers, thresholds, and configuration constants
to improve maintainability and reduce duplication.
"""

# ============================================================================
# THRESHOLD CONFIGURATION - Metric Alert Thresholds
# ============================================================================

DEFAULT_THRESHOLDS = {
    "cpu_load_1m": 0.80,              # Load average threshold
    "mem_used_percent": 85.0,          # Memory usage percentage
    "disk_used_percent": 90.0,         # Disk usage percentage
    "cpu_temp_c": 80.0,                # CPU temperature in Celsius
    "core_voltage_v": 1.30,            # Core voltage threshold
    "cpu_clock_mhz": 2200.0,           # CPU clock speed in MHz
    "uptime_seconds": 1209600.0,       # Uptime in seconds (14 days)
    "net_rx_kbps": 50000.0,            # Network RX in kbps
    "net_tx_kbps": 50000.0,            # Network TX in kbps
}

# ============================================================================
# HYSTERESIS CONFIGURATION - Alert Clearing Thresholds
# ============================================================================

HYSTERESIS = {
    "cpu_load_1m": 0.05,               # 5% drop required to clear alert
    "mem_used_percent": 5.0,
    "disk_used_percent": 5.0,
    "cpu_temp_c": 5.0,
    "core_voltage_v": 0.05,
    "cpu_clock_mhz": 100.0,
    "uptime_seconds": 3600.0,
    "net_rx_kbps": 5000.0,
    "net_tx_kbps": 5000.0,
}

# ============================================================================
# SEVERITY CALCULATION - Severity levels based on threshold exceedance
# ============================================================================

SEVERITY_WARNING_THRESHOLD = 0.10    # 10% above threshold = warning
SEVERITY_CRITICAL_THRESHOLD = 0.25   # 25% above threshold = critical
# Above critical threshold = severe

# ============================================================================
# POLLING CONFIGURATION
# ============================================================================

DEFAULT_POLLING_INTERVAL = 10        # Default polling interval in seconds
MIN_POLLING_INTERVAL = 5             # Minimum polling interval
MAX_POLLING_INTERVAL = 300           # Maximum polling interval (5 minutes)

# ============================================================================
# EXPONENTIAL BACKOFF CONFIGURATION
# ============================================================================

BACKOFF_BASE_DELAY = 1               # Initial backoff delay in seconds
BACKOFF_MAX_DELAY = 60               # Maximum backoff delay in seconds
BACKOFF_MAX_RETRIES = 5              # Maximum number of retries before offline

# ============================================================================
# NETWORK CONVERSION FACTORS
# ============================================================================

BYTES_TO_KBPS_FACTOR = 8.0           # Conversion: bytes/s to kbps
BYTES_TO_MB_FACTOR = 1000000.0       # Conversion: bytes to MB
BYTES_TO_KB_FACTOR = 1000.0          # Conversion: bytes to KB

# ============================================================================
# SECURITY & ENCRYPTION CONFIGURATION
# ============================================================================

# Argon2 password hashing parameters
ARGON2_TIME_COST = 20                # CPU iterations
ARGON2_MEMORY_COST = 65536           # Memory in KiB
ARGON2_PARALLELISM = 4               # Parallelism factor

# SSH Key configuration
SSH_KEY_TYPE = "ed25519"             # SSH key type
SSH_KEY_BITS = 4096                  # SSH key bits (if RSA)

# ============================================================================
# SYSTEM LIMITS & CONSTRAINTS
# ============================================================================

MAX_DEVICES = 100                    # Maximum number of monitored devices
MAX_HISTORICAL_ENTRIES = 1000        # Maximum cache entries per device
CONNECTION_TIMEOUT = 10              # SSH connection timeout in seconds
COMMAND_TIMEOUT = 30                 # Command execution timeout in seconds

# ============================================================================
# UI CONFIGURATION
# ============================================================================

UI_WIDTH = 1024                      # Default UI width in pixels
UI_HEIGHT = 600                      # Default UI height in pixels
UI_REFRESH_RATE = 30                 # UI refresh rate in FPS

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"

# ============================================================================
# FILE PATHS (Relative to project root)
# ============================================================================

CACHE_FILE = "data/cache_data.json"
DEVICE_LIST_FILE = "data/device_list.json"
LOG_FILE = "logs/system.log"

