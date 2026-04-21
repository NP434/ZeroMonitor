"""
ZeroMonitor - Agent-less Hardware Monitoring System

Entry point for the ZeroMonitor application.
Initializes logging, event bus, and all system modules.
"""

import time
import argparse
import os
import sys
import logging

# --- LOGGING SETUP (MUST BE FIRST) ---
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()  # Also print to terminal
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("ZeroMonitor System Starting")
logger.info("=" * 60)

# --- IMPORTS ---
from src.event_bus import EventBus
from src.driver import Driver
from src.datainterpreter import DataInterpreter
from src.network_manager import NetworkManager
from ui.display_ui import DisplayUI
from ui.control_ui import ControlUI
from Pairing.pairing_control import ControlPairing
from src.paths import Config

try:
    from security_manager import SecurityManager
    from update_manager import UpdateManager
except ImportError as e:
    logger.warning(f"Optional module not found: {e}")
    SecurityManager = None
    UpdateManager = None


def main():
    """Main entry point for ZeroMonitor application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="ZeroMonitor - Agent-less Hardware Monitoring System"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode (uses dev_vault instead of system paths)"
    )
    args = parser.parse_args()

    # Initialize configuration
    config = Config(dev_mode=args.dev)
    logger.info(f"Configuration loaded (dev_mode={args.dev})")

    # Create and start event bus
    bus = EventBus()
    bus.start()
    logger.info("Event bus started")

    # Initialize core modules
    driver = Driver(bus, config=config)
    driver.start()

    data_interpreter = DataInterpreter(bus, config=config, json_filepath=config.cache_file)
    logger.info("Data interpreter initialized")

    ui_control = ControlUI(bus, config=config)
    pair_control = ControlPairing(bus, config=config)

    if SecurityManager:
        security = SecurityManager(event_bus=bus, config=config)
    if UpdateManager:
        updater = UpdateManager(event_bus=bus, config=config)

    network = NetworkManager(bus=bus, config=config)

    # Start UI
    logger.info("Starting display UI")
    ui_display = DisplayUI(config=config, bus=bus, ui_control=ui_control)
    ui_display.run()

    # Main keep-alive loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        driver.stop_system()


if __name__ == "__main__":
    main()


