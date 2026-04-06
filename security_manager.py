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
        self.logger = logging.getLogger("Security")

        # Subscribe to the UI's security events
        self.bus.subscribe("CREATE_PASSCODE", self._handle_create_secrets)
        self.bus.subscribe("UNLOCK_VAULT", self._handle_unlock_vault)

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
        self.logger.info("Encrypted SSH keys generated.")

        # --- Create the Initial Device List ---
        self.logger.info("Creating initial device list...")
        device_list = {"node1": {"hostname": "127.0.0.1", "user": "admin", "name": "LocalTest"}}
        device_json = json.dumps(device_list).encode('utf-8')

        # --- Encrypt the Device List ---
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        encryption_key = base64.urlsafe_b64encode(kdf.derive(passcode_bytes))
        
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

            # Rebuild the key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(passcode_bytes))

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

        except Exception as e:
            error_str = str(e)
            self.logger.error(f"Decryption failed! Error: {e}")

            # Tell UI we failed
            self.bus.publish("UNLOCK_RESULT", {
                "success": False, 
                "error": error_str
            })