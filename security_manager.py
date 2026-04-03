import os
import json
import logging

class SecurityManager:
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config
        self.logger = logging.getLogger("security")

        # Subscribe to the UI's security events
        self.bus.subscribe("CREATE_PASSCODE", self._handle_create_secrets)
        self.bus.subscribe("UNLOCK_VAULT", self._handle_unlock_vault)

    def _handle_create_secrets(self, payload):
        """Equivalent to make_secrets.sh"""
        passcode = payload.get("passcode")
        self.logger.info("Initializing security protocols (First Boot)...")

        if self.config.dev_mode:
            self.logger.warning("DEV MODE: Bypassing actual SSH generation and encryption.")
            
            # 1. Fake the Encrypted SSH Key
            with open(self.config.ssh_key_enc, "w") as f:
                f.write("DUMMY_ENCRYPTED_SSH_KEY_DATA")
                
            # 2. Create the dummy device list directly into the dev_vault/ram
            # (Skipping encryption so the Driver can immediately read it)
            dummy_devices = {"node1": {"hostname": "127.0.0.1", "user": "admin", "name": "LocalTest"}}
            with open(self.config.decrypted_list, "w") as f:
                json.dump(dummy_devices, f)
                
            self.logger.info("DEV MODE: Dummy secrets created successfully.")
            
        else:
            self.logger.info("PROD MODE: Executing full cryptography generation...")
            # FUTURE: We will put the Python Cryptography logic here!

    def _handle_unlock_vault(self, payload):
        """Equivalent to startup_script.sh"""
        passcode = payload.get("passcode")
        self.logger.info("Unlocking vault...")

        if self.config.dev_mode:
            self.logger.warning("DEV MODE: Bypassing decryption.")
            # In dev mode, the unencrypted files are likely already in the dev_vault/ram
            self.logger.info("DEV MODE: Vault bypassed.")
            
        else:
            self.logger.info("PROD MODE: Executing full decryption...")
            # FUTURE: We will put the Python Decryption logic here!