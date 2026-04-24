import os
import json
import logging
import base64
import argon2
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet

class SecurityManager:
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config
        self.logger = logging.getLogger("Security")

        # Subscribe to the UI's security events
        self.bus.subscribe("CREATE_PASSCODE", self._handle_create_secrets)
        self.bus.subscribe("UNLOCK_VAULT", self._handle_unlock_vault)
        self.bus.subscribe("SYNC_VAULT", self._handle_sync_vault)

    def _handle_create_secrets(self, payload):
        """Generates SSH keys and encrypts the vault (Runs in ALL modes)"""
        passcode = payload.get("passcode")
        self.logger.info("Initializing security protocols...")
        
        passcode_bytes = passcode.encode('utf-8')

        # --- Generate and Encrypt SSH Key (Ed25519) ---
        self.logger.info("Generating SSH key pair...")
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        encrypted_ssh = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.BestAvailableEncryption(passcode_bytes)
        )
        
        with open(self.config.ssh_key_enc, "wb") as f:
            f.write(encrypted_ssh)
        self.logger.info("Encrypted SSH key generated.")

        # --- Process the Public Key (Unencrypted) ---
        public_key = private_key.public_key()
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        # Save the public key to disk (Ensure self.config.ssh_pub_key exists in paths.py)
        with open(self.config.ssh_pub_key, "wb") as f:
            f.write(public_ssh)
            
        self.logger.info("Public SSH key generated.")

        # --- Create the Initial Device List ---
        self.logger.info("Creating initial device list...")
        device_list = {"node1": {"hostname": "127.0.0.1", "user": "admin", "name": "LocalTest"}}
        device_json = json.dumps(device_list).encode('utf-8')

        # --- Encrypt the Device List ---
        salt = os.urandom(16)
        raw_key = argon2.low_level.hash_secret_raw(
            secret=passcode_bytes,
            salt=salt,
            time_cost=6,          # CPU Iterations
            memory_cost=65536,    # 64 MB of RAM
            parallelism=4,        # Use all 4 Cortex-A53 cores
            hash_len=32,          # Fernet requires exactly 32 bytes
            type=argon2.low_level.Type.ID 
        )
        encryption_key = base64.urlsafe_b64encode(raw_key)

        fernet = Fernet(encryption_key)
        encrypted_data = fernet.encrypt(device_json)
        
        with open(self.config.encrypted_list, "wb") as f:
            f.write(salt + encrypted_data)
            
        self.logger.info("Encrypted device list created.")
        self.logger.info("--- Secrets Created Successfully ---")

        # Automatically unlock and load into RAM for the current session
        self._handle_unlock_vault(payload)


    def _handle_unlock_vault(self, payload):
        """Decrypts the vault using the provided passcode (Runs in ALL modes)"""
        passcode = payload.get("passcode")
        self.logger.info("Unlocking vault...")
        
        passcode_bytes = passcode.encode('utf-8')

        try:
            # Read the encrypted file
            with open(self.config.encrypted_list, "rb") as f:
                file_data = f.read()

            # Separate salt and encrypted data
            salt = file_data[:16]
            encrypted_data = file_data[16:]

            # Rebuild the key using Argon2
            raw_key = argon2.low_level.hash_secret_raw(
                secret=passcode_bytes,
                salt=salt,
                time_cost=6,          
                memory_cost=65536,    
                parallelism=4,        
                hash_len=32,          
                type=argon2.low_level.Type.ID 
            )
            encryption_key = base64.urlsafe_b64encode(raw_key)
            
            # Save key for JSON Encryption
            self._session_key = encryption_key
            self._session_salt = salt

            # Decrypt
            fernet = Fernet(encryption_key)
            decrypted_json_bytes = fernet.decrypt(encrypted_data)

            # Save to the active memory/dev folder
            with open(self.config.decrypted_list, "wb") as f:
                f.write(decrypted_json_bytes)

            # --- Decrypt the SSH Key ---
            with open(self.config.ssh_key_enc, "rb") as f:
                encrypted_ssh_data = f.read()

            # Load the OpenSSH format key using the passcode to unlock it
            private_key = serialization.load_ssh_private_key(
                encrypted_ssh_data,
                password=passcode_bytes
            )

            # Re-serialize it WITHOUT encryption for the RAM drive
            unencrypted_ssh = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption()
            )

            # Save to the RAM drive
            with open(self.config.ssh_key_ram, "wb") as f:
                f.write(unencrypted_ssh)

            self.logger.info("--- Secrets Decrypted Successfully ---")
            # Tell UI we succeeded 
            self.bus.publish("UNLOCK_RESULT", {"success": True})
            # Load Devices safely using Dev Mode paths
            if os.path.exists(self.config.decrypted_list):
                with open(self.config.decrypted_list, "r", encoding='utf-8') as file:
                    device_data = json.load(file)
            self.bus.publish("DEVICE_LIST_UPDATED", device_data)

        except Exception as e:
            error_str = str(e)
            self.logger.error(f"Decryption failed! Error: {e}")

            # Tell UI we failed
            self.bus.publish("UNLOCK_RESULT", {
                "success": False, 
                "error": error_str
            })

    def _handle_sync_vault(self, payload=None):
        """Reads the unencrypted RAM device list and safely encrypts it back to storage."""
        ### self.app.bus.publish("SYNC_VAULT", {}) # Update Encrypted JSON
        if not self._session_key or not self._session_salt:
            self.logger.error("Cannot sync vault: No active security session.")
            return

        self.logger.info("Syncing updated device list to secure storage...")

        try:
            # Read the updated JSON from RAM
            with open(self.config.decrypted_list, "rb") as f:
                raw_json_bytes = f.read()

            # Encrypt using the active session key
            fernet = Fernet(self._session_key)
            encrypted_data = fernet.encrypt(raw_json_bytes)

            # Write back to storage (Must prepend the salt so it can be unlocked next boot!)
            with open(self.config.encrypted_list, "wb") as f:
                f.write(self._session_salt + encrypted_data)

            self.logger.info("Vault sync complete.")

        except Exception as e:
            self.logger.error(f"Failed to sync vault: {e}")