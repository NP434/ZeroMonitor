import os
import sys

class Config:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        
        # Root Directories
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if self.dev_mode:
            # dev_mode argparse repos
            self.storage_dir = os.path.join(self.base_dir, "dev_vault", "storage")
            self.ram_dir = os.path.join(self.base_dir, "dev_vault", "ram")
        else:
            # Standard Raspberry Pi paths
            self.storage_dir = "/home/zero_monitor_storage"
            self.ram_dir = "/run/zero_monitor_decrypted"

        # Specific File Paths
        self.encrypted_list = os.path.join(self.storage_dir, "encrypted_device_list.enc")
        self.decrypted_list = os.path.join(self.ram_dir, "device_list.json")
        self.ssh_key_enc = os.path.join(self.storage_dir, "id_ed25519.enc")
        self.ssh_key_ram = os.path.join(self.ram_dir, "decrypted_key")
        self.pass_file = os.path.join(self.ram_dir, "zero_pass.txt")
        self.pairing_info = os.path.join(self.storage_dir, "pairing_info.json")
        self.server_cert = os.path.join(self.storage_dir, "server.crt")
        self.server_key = os.path.join(self.storage_dir, "server.key")
        self.cache_file = os.path.join(self.storage_dir, "cache_data.json")
        self.email_settings = os.path.join(self.storage_dir, "email_settings.json")
        self.ssh_pub_key = os.path.join(self.storage_dir, "id_ed25519.pub")

        # Ensure directories exist
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.ram_dir, exist_ok=True)