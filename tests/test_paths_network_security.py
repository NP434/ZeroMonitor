import json
import os
import subprocess

import network_manager
from network_manager import NetworkManager
from paths import Config
from security_manager import SecurityManager


def test_config_dev_mode_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = Config(dev_mode=True)
    assert cfg.dev_mode is True
    assert os.path.isdir(cfg.storage_dir)
    assert os.path.isdir(cfg.ram_dir)
    assert cfg.decrypted_list.endswith("device_list.json")


def test_config_prod_paths_without_real_fs(monkeypatch):
    created = []
    monkeypatch.setattr("paths.os.makedirs", lambda p, exist_ok=False: created.append((p, exist_ok)))
    cfg = Config(dev_mode=False)
    assert cfg.storage_dir == "/home/zero_monitor_storage"
    assert cfg.ram_dir == "/run/zero_monitor_decrypted"
    assert len(created) == 2


def test_network_manager_dev_mode(fake_bus, temp_config, monkeypatch):
    nm = NetworkManager(fake_bus, temp_config)
    monkeypatch.setattr(network_manager.time, "sleep", lambda *_: None)

    nm._handle_connect({"ssid": "wifi", "password": "ok"})
    nm._handle_connect({"ssid": "wifi", "password": "fail"})

    results = [p for n, p in fake_bus.published if n == "WIFI_RESULT"]
    assert results[0]["success"] is True
    assert results[1]["success"] is False


def test_network_manager_prod_paths(fake_bus, temp_config, monkeypatch):
    temp_config.dev_mode = False
    nm = NetworkManager(fake_bus, temp_config)

    class Result:
        def __init__(self, rc, stderr=""):
            self.returncode = rc
            self.stderr = stderr

    monkeypatch.setattr(network_manager.subprocess, "run", lambda *a, **k: Result(0, ""))
    nm._handle_connect({"ssid": "wifi", "password": "ok"})

    monkeypatch.setattr(network_manager.subprocess, "run", lambda *a, **k: Result(1, "bad pwd"))
    nm._handle_connect({"ssid": "wifi", "password": "bad"})

    def _timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="nmcli", timeout=1)

    monkeypatch.setattr(network_manager.subprocess, "run", _timeout)
    nm._handle_connect({"ssid": "wifi", "password": "x"})

    monkeypatch.setattr(network_manager.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    nm._handle_connect({"ssid": "wifi", "password": "x"})

    assert len([n for n, _ in fake_bus.published if n == "WIFI_RESULT"]) == 4


def test_security_manager_create_unlock_sync(fake_bus, temp_config):
    sm = SecurityManager(fake_bus, temp_config)

    sm._handle_create_secrets({"passcode": "1234"})
    assert os.path.exists(temp_config.ssh_key_enc)
    assert os.path.exists(temp_config.ssh_pub_key)
    assert os.path.exists(temp_config.encrypted_list)
    assert os.path.exists(temp_config.decrypted_list)
    assert os.path.exists(temp_config.ssh_key_ram)

    unlock_results = [p for n, p in fake_bus.published if n == "UNLOCK_RESULT"]
    assert unlock_results[-1]["success"] is True

    with open(temp_config.decrypted_list, "w", encoding="utf-8") as f:
        json.dump({"node": {"name": "A"}}, f)
    sm._handle_sync_vault()
    assert os.path.exists(temp_config.encrypted_list)


def test_security_manager_unlock_failure_and_sync_without_session(fake_bus, temp_config):
    sm = SecurityManager(fake_bus, temp_config)
    sm._handle_unlock_vault({"passcode": "bad"})

    unlock_results = [p for n, p in fake_bus.published if n == "UNLOCK_RESULT"]
    assert unlock_results[-1]["success"] is False

    # no session: should safely return
    sm._session_key = None
    sm._session_salt = None
    sm._handle_sync_vault()


def test_security_manager_subscriptions(fake_bus, temp_config):
    SecurityManager(fake_bus, temp_config)
    assert "CREATE_PASSCODE" in fake_bus.subscriptions
    assert "UNLOCK_VAULT" in fake_bus.subscriptions
    assert "SYNC_VAULT" in fake_bus.subscriptions


def test_security_manager_sync_failure_logs(fake_bus, temp_config, monkeypatch):
    sm = SecurityManager(fake_bus, temp_config)
    sm._session_key = b"x" * 32
    sm._session_salt = b"salt"
    logs = []
    monkeypatch.setattr(sm.logger, "error", lambda msg: logs.append(msg))
    temp_config.decrypted_list = "/tmp/definitely_missing_zero_monitor_sync.json"
    sm._handle_sync_vault()
    assert any("Failed to sync vault" in msg for msg in logs)


def test_update_manager_dev_mode(fake_bus, temp_config, monkeypatch):
    from update_manager import UpdateManager
    um = UpdateManager(fake_bus, temp_config)
    assert "CHECK_FOR_UPDATE" in fake_bus.subscriptions
    assert "APPLY_UPDATE" in fake_bus.subscriptions

    # Dev mode check
    um._handle_check()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "up_to_date"

    # Dev mode apply
    um._handle_apply()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "update_failed"


def test_update_manager_prod_mode(fake_bus, temp_config, monkeypatch):
    temp_config.dev_mode = False
    from update_manager import UpdateManager
    um = UpdateManager(fake_bus, temp_config)

    # Mock subprocess for check
    class MockRun:
        def __init__(self, stdout=""):
            self.stdout = stdout
            self.returncode = 0

    monkeypatch.setattr("update_manager.subprocess.run", lambda *a, **k: MockRun("abc123\n"))
    um._handle_check()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "up_to_date"

    # Different hashes
    calls = []
    def mock_run(cmd, **k):
        calls.append(cmd)
        if cmd == ["git", "rev-parse", "HEAD"]:
            return MockRun("local\n")
        elif cmd == ["git", "rev-parse", "@{u}"]:
            return MockRun("remote\n")
        else:
            return MockRun()
    monkeypatch.setattr("update_manager.subprocess.run", mock_run)
    um._handle_check()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "available"

    # Exception in check
    monkeypatch.setattr("update_manager.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("git fail")))
    um._handle_check()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "error"

    # Apply success
    temp_config.dev_mode = False
    calls = []
    monkeypatch.setattr("update_manager.subprocess.run", lambda cmd, **k: calls.append(cmd) or MockRun())
    monkeypatch.setattr("update_manager.pygame.quit", lambda: None)
    monkeypatch.setattr("update_manager.os._exit", lambda c: None)
    um._handle_apply()
    assert "git" in str(calls)

    # Apply exception
    monkeypatch.setattr("update_manager.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("pull fail")))
    um._handle_apply()
    published = [p for n, p in fake_bus.published if n == "UPDATE_STATUS"]
    assert published[-1]["status"] == "update_failed"
