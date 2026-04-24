import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
from types import SimpleNamespace

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def pygame_headless():
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


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
        base_dir=os.getcwd(),
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
        ui_settings=str(storage / "ui_settings.json"),
    )

    with open(cfg.decrypted_list, "w", encoding="utf-8") as f:
        json.dump({}, f)

    return cfg


@pytest.fixture
def ui_surface():
    return pygame.Surface((1024, 600))


@pytest.fixture
def ui_app(fake_bus, temp_config):
    class DummyUIControl:
        def __init__(self, bus):
            self.bus = bus
            self.added = []
            self.stopped = False

        def add_node(self, node_config):
            self.added.append(node_config)
            self.bus.publish("UI_ADD_NODE", node_config)

        def stop_system(self):
            self.stopped = True
            self.bus.publish("STOP_SYSTEM", None)

    class DummyApp(SimpleNamespace):
        def __init__(self):
            super().__init__(
                width=1024,
                height=600,
                bus=fake_bus,
                config=temp_config,
                ui_control=DummyUIControl(fake_bus),
                changed_screens=[],
            )

        def change_screen(self, name):
            self.changed_screens.append(name)

    return DummyApp()
