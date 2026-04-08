import json
from types import SimpleNamespace

import pytest


class FakeBus:
    def __init__(self):
        self.subscriptions = {}
        self.published = []
        self.stopped = False

    def subscribe(self, event_type, handler):
        self.subscriptions.setdefault(event_type, []).append(handler)

    def publish(self, event_type, payload=None):
        self.published.append((event_type, payload))

    def stop(self):
        self.stopped = True


@pytest.fixture
def fake_bus():
    return FakeBus()


@pytest.fixture
def temp_config(tmp_path):
    storage = tmp_path / "storage"
    ram = tmp_path / "ram"
    storage.mkdir()
    ram.mkdir()

    cfg = SimpleNamespace(
        dev_mode=True,
        storage_dir=str(storage),
        ram_dir=str(ram),
        encrypted_list=str(storage / "encrypted_device_list.enc"),
        decrypted_list=str(ram / "device_list.json"),
        ssh_key_enc=str(storage / "id_ed25519.enc"),
        ssh_key_ram=str(ram / "decrypted_key"),
        ssh_pub_key=str(storage / "id_ed25519.pub"),
        cache_file=str(storage / "cache_data.json"),
        pass_file=str(ram / "zero_pass.txt"),
        pairing_info=str(storage / "pairing_info.json"),
        server_cert=str(storage / "server.crt"),
        server_key=str(storage / "server.key"),
        email_settings=str(storage / "email_settings.json"),
    )

    with open(cfg.decrypted_list, "w", encoding="utf-8") as f:
        json.dump({}, f)

    return cfg

