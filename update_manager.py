import subprocess
import sys
import logging
import time
import os
import pygame

#PUT IN: sudo git config --global --add safe.directory /home/admin/ZeroMonitor

class UpdateManager:
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config
        self.logger = logging.getLogger("Updater")

        # Subscribe to UI commands
        self.bus.subscribe("CHECK_FOR_UPDATE", self._handle_check)
        self.bus.subscribe("APPLY_UPDATE", self._handle_apply)

    def _handle_check(self, payload=None):
        """Checks GitHub and publishes the result back to the UI"""
        self.logger.info("Checking for updates...")
        
        # Dev Mode Bypass
        if self.config.dev_mode:
            self.logger.info("[DEV MODE] Bypassing GitHub check. Simulating 'Up to date'")
            time.sleep(1) # Small delay so you can actually see the UI screen doing something
            self.bus.publish("UPDATE_STATUS", {"status": "up_to_date"})
            return

        try:
            # Assuming self.config.base_dir is the absolute path to your repo (e.g., /home/admin/ZeroMonitor)
            repo_path = self.config.base_dir

            subprocess.run(["git", "fetch"], check=True, capture_output=True, cwd=repo_path)
            local_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            remote_hash = subprocess.run(["git", "rev-parse", "@{u}"], capture_output=True, text=True).stdout.strip()

            if local_hash != remote_hash:
                self.logger.info("Update available!")
                self.bus.publish("UPDATE_STATUS", {"status": "available"})
            else:
                self.logger.info("System is up to date.")
                self.bus.publish("UPDATE_STATUS", {"status": "up_to_date"})

        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            self.bus.publish("UPDATE_STATUS", {"status": "error", "message": str(e)})

    def _handle_apply(self, payload=None):
        """Pulls the latest code and reboots the Python script."""
        # Dev Mode Bypass
        if self.config.dev_mode:
            self.logger.warning("[DEV MODE] Update blocked to protect local code.")
            self.bus.publish("UPDATE_STATUS", {"status": "update_failed"})
            return

        self.logger.info("Pulling latest update from GitHub...")
        try:
            # Assuming you added cwd=self.config.base_dir based on the last step
            subprocess.run(["git", "pull"], check=True, capture_output=True, cwd=self.config.base_dir)
            self.logger.info("Update successful! Rebooting application...")
            
            # Release the KMS/DRM hardware display lock
            pygame.quit() 
            
            # Hard-kill the entire application, bypassing any event bus threads
            os._exit(0) 

        except Exception as e:
            self.logger.error(f"Failed to pull update: {e}")
            self.bus.publish("UPDATE_STATUS", {"status": "update_failed"})