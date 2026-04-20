import subprocess
import logging
import time

class NetworkManager:
    def __init__(self, bus, config):
        self.bus = bus
        self.config = config
        self.logger = logging.getLogger("Network")
        
        # Subscribe to the UI's request to connect
        self.bus.subscribe("WIFI_CONNECT_REQ", self._handle_connect)

    def _handle_connect(self, data):
        ssid = data.get("ssid")
        password = data.get("password")
        
        self.logger.info(f"Attempting to connect to SSID: {ssid}")
        
        # --- DEV MODE: Simulation ---
        if self.config.dev_mode:
            self.logger.info("DEV MODE: Simulating network handshake...")
            time.sleep(2) # Give it a realistic delay
            
            # Use a dummy rule for testing: "fail" as a password triggers an error
            success = (password != "fail")
            error_msg = "Invalid Passphrase" if not success else ""
            
            self.bus.publish("WIFI_RESULT", {"success": success, "error": error_msg})
            
        # --- PROD MODE: Real Raspberry Pi Logic ---
        else:
            try:
                # nmcli dev wifi connect <SSID> password <PASSWORD>
                cmd = ["nmcli", "dev", "wifi", "connect", ssid, "password", password]
                
                # We use a timeout so it doesn't hang forever if the router is slow
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                success = result.returncode == 0
                error_msg = result.stderr if not success else ""
                
                if success:
                    self.logger.info(f"Successfully connected to {ssid}")
                else:
                    self.logger.error(f"Connection failed: {error_msg}")

                self.bus.publish("WIFI_RESULT", {"success": success, "error": error_msg})

            except subprocess.TimeoutExpired:
                self.logger.error("WiFi connection timed out.")
                self.bus.publish("WIFI_RESULT", {"success": False, "error": "Connection Timed Out"})
            except Exception as e:
                self.logger.error(f"Unexpected networking error: {e}")
                self.bus.publish("WIFI_RESULT", {"success": False, "error": str(e)})