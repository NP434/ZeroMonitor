import os
import json
import logging
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

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
            passcode_bytes = passcode.encode('utf-8')

            # --- Generate and Encrypt SSH Key (Ed25519) ---
            self.logger.info("Generating SSH key pair...")
            private_key = ed25519.Ed25519PrivateKey.generate()
            
            # Serialize into OpenSSH format and encrypt with the user's passcode
            encrypted_ssh = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.BestAvailableEncryption(passcode_bytes)
            )
            
            with open(self.config.ssh_key_enc, "wb") as f:
                f.write(encrypted_ssh)
            self.logger.info("Encrypted SSH keys generated.")

            # --- Create the Initial Device List ---
            self.logger.info("Creating initial device list...")
            device_list = {"node1": {"hostname": "127.0.0.1", "user": "admin", "name": "LocalTest"}}
            device_json = json.dumps(device_list).encode('utf-8')

            # --- Encrypt the Device List ---
            # We use PBKDF2 to stretch the passcode into a secure 32-byte key
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(passcode_bytes))
            
            # Encrypt the JSON data using Fernet (AES-128-CBC + HMAC for integrity)
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(device_json)
            
            # We save the salt AND the encrypted data together so we can decrypt it later
            with open(self.config.encrypted_list, "wb") as f:
                f.write(salt + encrypted_data)
                
            self.logger.info("Encrypted device list created.")
            self.logger.info("--- Secrets Created ---")

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