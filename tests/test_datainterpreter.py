import json

import datainterpreter as di
from datainterpreter import DataInterpreter


class DummyMetricEvent:
    def __init__(self, node="node1", success=True, payload=None, timestamp="2026-01-01T00:00:00"):
        self.node = node
        self.success = success
        self.payload = payload or {}
        self.timestamp = timestamp


def _mk_interpreter(fake_bus, temp_config, tmp_path, **kwargs):
    return DataInterpreter(
        fake_bus,
        temp_config,
        json_filepath=str(tmp_path / "cache.json"),
        **kwargs,
    )


def test_threshold_config(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    itp.set_threshold("cpu_temp_c", 90)
    itp.set_thresholds_for_device("node1", {"cpu_temp_c": 75})
    t = itp._get_thresholds_for_node("node1")
    assert t["cpu_temp_c"] == 75


def test_process_and_severity_and_write_online(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    event = DummyMetricEvent(
        payload={
            "cpu_load_1m": 0.95,
            "cpu_temp_c": 85,
            "mem_used_mb": 80,
            "mem_total_mb": 100,
            "disk_used_percent": 95,
            "core_voltage_v": 1.4,
            "cpu_clock_mhz": 2500,
            "uptime_seconds": 9999999,
            "net_rx_kbps": 60000,
            "net_tx_kbps": 100,
        }
    )

    interpreted = itp.process_data(event)
    assert interpreted["metrics"]["mem_used_percent"] == 80.0

    interpreted = itp._annotate_severity(interpreted)
    assert interpreted["severities"]["cpu_temp_c"] in {"warning", "critical", "severe"}

    interpreted["status"] = "online"
    interpreted["success"] = True
    interpreted["error"] = "old"
    itp._write_to_json_file(interpreted)

    with open(itp.json_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "error" not in data["node1"]
    assert data["node1"]["last_success_timestamp"] == data["node1"]["timestamp"]


def test_offline_payload_and_interpret_failure(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)

    # seed existing metrics for offline payload copy
    itp._write_to_json_file(
        {
            "node": "node1",
            "timestamp": "t0",
            "status": "online",
            "success": True,
            "metrics": {"cpu_temp_c": 50},
            "severities": {"cpu_temp_c": "normal"},
        }
    )

    fail_event = DummyMetricEvent(success=False, payload={"error": "ssh failed"}, timestamp="t1")
    itp.interpret_data(fail_event)

    assert ("device_offline", {
        "node": "node1",
        "timestamp": "t1",
        "status": "offline",
        "success": False,
        "error": "ssh failed",
        "last_success_timestamp": "t0",
        "metrics": {"cpu_temp_c": 50},
        "severities": {"cpu_temp_c": "normal"},
    }) in fake_bus.published


def test_interpret_success_publishes_alerts(fake_bus, temp_config, tmp_path, monkeypatch):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    sent = []
    monkeypatch.setattr(itp, "_send_warning_email", lambda interpreted: sent.append(interpreted["node"]))

    event = DummyMetricEvent(
        payload={
            "cpu_load_1m": 0.95,
            "cpu_temp_c": 10,
            "mem_used_mb": 50,
            "mem_total_mb": 100,
            "disk_used_percent": 20,
            "core_voltage_v": None,
            "cpu_clock_mhz": None,
            "uptime_seconds": None,
            "net_rx_kbps": None,
            "net_tx_kbps": None,
        }
    )

    itp.interpret_data(event)

    names = [n for n, _ in fake_bus.published]
    assert "data_interpreted" in names
    assert "threshold_alert" in names
    assert sent == ["node1"]


def test_load_cache_entries_invalid_json(fake_bus, temp_config, tmp_path):
    fp = tmp_path / "broken.json"
    fp.write_text("not-json", encoding="utf-8")
    itp = DataInterpreter(fake_bus, temp_config, json_filepath=str(fp))
    assert itp._load_cache_entries() == {}


def test_write_offline_event_method(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    evt = DummyMetricEvent(success=False, payload={}, timestamp="tx")
    itp._write_offline_event_to_json(evt)
    with open(itp.json_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["node1"]["status"] == "offline"


def test_send_warning_email_ssl_and_starttls(fake_bus, temp_config, tmp_path, monkeypatch):
    calls = []

    class SMTPSSL:
        def __init__(self, host, port, context=None):
            calls.append(("ssl", host, port, context is not None))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, pwd):
            calls.append(("login", user, pwd))

        def send_message(self, msg):
            calls.append(("send", msg["Subject"]))

    class SMTP:
        def __init__(self, host, port):
            calls.append(("smtp", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context=None):
            calls.append(("starttls", context is not None))

        def login(self, user, pwd):
            calls.append(("login2", user, pwd))

        def send_message(self, msg):
            calls.append(("send2", msg["Subject"]))

    monkeypatch.setattr(di.smtplib, "SMTP_SSL", SMTPSSL)
    monkeypatch.setattr(di.smtplib, "SMTP", SMTP)

    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    itp._send_warning_email({"node": "n1"})

    itp2 = _mk_interpreter(fake_bus, temp_config, tmp_path, smtp_port=587)
    itp2._send_warning_email({"node": "n2"})

    assert any(c[0] == "ssl" for c in calls)
    assert any(c[0] == "starttls" for c in calls)


def test_calculate_severity_and_threshold_clear(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    assert itp._calculate_severity(1, 0) == "warning"
    assert itp._calculate_severity(1.05, 1.0) == "warning"
    assert itp._calculate_severity(1.2, 1.0) == "critical"
    assert itp._calculate_severity(1.3, 1.0) == "severe"

    interpreted = {
        "node": "n",
        "metrics": {"cpu_temp_c": 100},
    }
    trig, clr = itp.check_thresholds(interpreted)
    assert trig and not clr

    interpreted2 = {
        "node": "n",
        "metrics": {"cpu_temp_c": 70},
    }
    trig2, clr2 = itp.check_thresholds(interpreted2)
    assert not trig2 and clr2


def test_interpret_failure_logs_when_offline_write_fails(fake_bus, temp_config, tmp_path, monkeypatch):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    logs = []
    monkeypatch.setattr(di.logging, "error", lambda msg: logs.append(msg))
    monkeypatch.setattr(itp, "_write_to_json_file", lambda *_: (_ for _ in ()).throw(RuntimeError("bad write")))

    itp.interpret_data(DummyMetricEvent(success=False, payload={"error": "x"}))
    assert any("Failed to write offline event" in msg for msg in logs)


def test_interpret_success_prints_json_and_email_errors(fake_bus, temp_config, tmp_path, monkeypatch):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    printed = []
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(" ".join(str(a) for a in args)))
    monkeypatch.setattr(itp, "_write_to_json_file", lambda *_: (_ for _ in ()).throw(RuntimeError("json boom")))
    monkeypatch.setattr(itp, "_send_warning_email", lambda *_: (_ for _ in ()).throw(RuntimeError("mail boom")))

    itp.interpret_data(DummyMetricEvent(payload={
        "cpu_load_1m": 0.95,
        "cpu_temp_c": 81,
        "mem_used_mb": 9,
        "mem_total_mb": 10,
        "disk_used_percent": 91,
    }))
    assert any("JSON write error" in p for p in printed)
    assert any("Email error" in p for p in printed)


def test_threshold_cleared_event_is_published(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    first = DummyMetricEvent(payload={"cpu_temp_c": 100, "mem_total_mb": 10, "mem_used_mb": 1})
    second = DummyMetricEvent(payload={"cpu_temp_c": 70, "mem_total_mb": 10, "mem_used_mb": 1}, timestamp="2026-01-01T00:00:01")
    itp.interpret_data(first)
    itp.interpret_data(second)
    assert any(name == "threshold_cleared" for name, _ in fake_bus.published)


def test_ensure_cache_directory_and_none_node_write(fake_bus, temp_config, tmp_path):
    nested = tmp_path / "deep" / "cache.json"
    itp = DataInterpreter(fake_bus, temp_config, json_filepath=str(nested))
    itp._ensure_cache_directory()
    assert nested.parent.exists()

    itp._write_to_json_file({"timestamp": "x"})
    assert not nested.exists()


def test_load_cache_entries_for_non_dict_json(fake_bus, temp_config, tmp_path):
    fp = tmp_path / "list.json"
    fp.write_text("[]", encoding="utf-8")
    itp = DataInterpreter(fake_bus, temp_config, json_filepath=str(fp))
    assert itp._load_cache_entries() == {}


def test_send_warning_email_returns_without_config(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(
        fake_bus,
        temp_config,
        tmp_path,
        smtp_server=None,
        smtp_port=None,
        email_from=None,
        email_to=None,
    )
    assert itp._send_warning_email({"node": "n"}) is None


def test_send_warning_email_logs_failure(fake_bus, temp_config, tmp_path, monkeypatch):
    class BrokenSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            raise RuntimeError("smtp broke")

        def __exit__(self, *args):
            return False

    logs = []
    monkeypatch.setattr(di.smtplib, "SMTP_SSL", BrokenSMTP)
    monkeypatch.setattr(di.logging, "error", lambda msg: logs.append(msg))

    itp = _mk_interpreter(fake_bus, temp_config, tmp_path)
    itp._send_warning_email({"node": "n"})
    assert any("Failed to send warning email" in msg for msg in logs)


def test_send_warning_email_uses_configured_email_settings(fake_bus, temp_config, tmp_path, monkeypatch):
    sent_to = []

    class SMTPSSL:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, *args, **kwargs):
            return None

        def send_message(self, msg):
            sent_to.append(msg["To"])

    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump(
            {
                "email_configured": True,
                "email_address": "configured@example.com",
                "email_opt_out": False,
            },
            f,
        )

    monkeypatch.setattr(di.smtplib, "SMTP_SSL", SMTPSSL)

    itp = _mk_interpreter(fake_bus, temp_config, tmp_path, email_to="fallback@example.com")
    itp._send_warning_email({"node": "n"})

    assert sent_to == ["configured@example.com"]


def test_send_warning_email_skips_when_email_settings_opt_out(fake_bus, temp_config, tmp_path, monkeypatch):
    calls = []

    class SMTPSSL:
        def __init__(self, *args, **kwargs):
            calls.append("init")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, *args, **kwargs):
            calls.append("login")

        def send_message(self, msg):
            calls.append(msg["To"])

    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump(
            {
                "email_configured": False,
                "email_address": "",
                "email_opt_out": True,
            },
            f,
        )

    monkeypatch.setattr(di.smtplib, "SMTP_SSL", SMTPSSL)

    itp = _mk_interpreter(fake_bus, temp_config, tmp_path, email_to="fallback@example.com")
    assert itp._send_warning_email({"node": "n"}) is None
    assert calls == []


def test_resolve_email_recipient_falls_back_when_settings_missing(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path, email_to="fallback@example.com")
    assert itp._resolve_email_recipient() == "fallback@example.com"


def test_resolve_email_recipient_branch_paths(fake_bus, temp_config, tmp_path):
    itp = _mk_interpreter(fake_bus, temp_config, tmp_path, email_to="fallback@example.com")

    # Invalid JSON should fall back.
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        f.write("not-json")
    assert itp._resolve_email_recipient() == "fallback@example.com"

    # Non-dict JSON should also fall back.
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump(["not", "a", "dict"], f)
    assert itp._resolve_email_recipient() == "fallback@example.com"

    # Explicit email keys without a valid configured address should disable sending.
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump({"email_configured": True, "email_address": ""}, f)
    assert itp._resolve_email_recipient() is None

    # Settings with no email keys should use fallback recipient.
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump({"some_other_setting": True}, f)
    assert itp._resolve_email_recipient() == "fallback@example.com"


