import json
from types import SimpleNamespace

import driver as drv
from driver import Driver, load_targets


class DummyPollingAgent:
    def __init__(self, queue):
        self.queue = queue
        self.workers = {}
        self.launched = None
        self.reconciled = None
        self.removed = []
        self.shutdown_called = False

    def launch_nodes(self, nodes):
        self.launched = nodes

    def reconcile(self, nodes):
        self.reconciled = nodes

    def remove_node(self, name):
        self.removed.append(name)

    def shutdown(self):
        self.shutdown_called = True


class DummyExecutor:
    def __init__(self, *_, **__):
        self.submitted = []
        self.shutdown_called = False

    def submit(self, fn):
        self.submitted.append(fn)

    def shutdown(self, wait=True, cancel_futures=True):
        self.shutdown_called = True


def _write_devices(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_driver_start_and_stop(fake_bus, temp_config, monkeypatch):
    monkeypatch.setattr(drv, "PollingAgent", DummyPollingAgent)
    monkeypatch.setattr(drv, "ThreadPoolExecutor", DummyExecutor)
    monkeypatch.setattr(drv, "load_targets", lambda _cfg: ["n1"])

    d = Driver(fake_bus, temp_config)
    d.start()

    assert d.running is True
    assert d.polling_agent.launched == ["n1"]
    assert "UPDATE_POLLING_RATE" in fake_bus.subscriptions

    d.stop_system()
    assert d.running is False
    assert d.polling_agent.shutdown_called is True


def test_driver_update_polling_rate_add_remove_reload_and_name(fake_bus, temp_config, monkeypatch):
    data = {
        "k1": {"name": "A", "polling_frequency": 5, "hostname": "h", "user": "u", "operating_system": "linux"},
    }
    _write_devices(temp_config.decrypted_list, data)

    d = Driver(fake_bus, temp_config)
    d.polling_agent = DummyPollingAgent(None)
    monkeypatch.setattr(drv, "load_targets", lambda _cfg: ["x"])

    d.update_polling_rate({"host": "A", "poll_rate": 12})
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        updated = json.load(f)
    assert updated["k1"]["polling_frequency"] == 12
    assert ("ACK_UPDATE_POLLING_RATE", {"host": "A", "poll_rate": 12}) in fake_bus.published

    d.add_node({"name": "B", "hostname": "h2", "user": "u2", "operating_system": "linux", "polling_frequency": 3})
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        after_add = json.load(f)
    assert any(v.get("name") == "B" for v in after_add.values())

    d.remove_node("B")
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        after_remove = json.load(f)
    assert not any(v.get("name") == "B" for v in after_remove.values())

    d.update_device_name({"old_name": "A", "new_name": "AA"})
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        after_rename = json.load(f)
    assert any(v.get("name") == "AA" for v in after_rename.values())


def test_driver_pause_dispatch_and_handle_remove(fake_bus, temp_config):
    _write_devices(temp_config.decrypted_list, {"k1": {"name": "A", "polling_paused": False}})
    d = Driver(fake_bus, temp_config)
    d.polling_agent = DummyPollingAgent(None)
    node = SimpleNamespace(polling_paused=False)
    d.polling_agent.workers["A"] = (node, None)

    d._on_pause_polling({"device": "A", "paused": True})
    assert node.polling_paused is True
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        persisted = json.load(f)
    assert persisted["k1"]["polling_paused"] is True

    d._on_pause_polling({"device": "missing", "paused": True})

    d.remove_node = lambda name: fake_bus.publish("REMOVED", name)
    d._handle_remove_node({"node": "A"})
    assert ("REMOVED", "A") in fake_bus.published

    d.metrics_queue = SimpleNamespace(get=lambda timeout: "evt")
    d.running = True

    def publish_and_stop(name, payload):
        fake_bus.published.append((name, payload))
        d.running = False

    d.event_bus.publish = publish_and_stop
    d._dispatch_metrics()
    assert ("METRIC_EVENT", "evt") in fake_bus.published


def test_load_targets_variants(temp_config, monkeypatch):
    _write_devices(
        temp_config.decrypted_list,
        {
            "n1": {"hostname": "h", "user": "u", "name": "L", "operating_system": "linux", "polling_frequency": 2, "polling_paused": True},
            "n2": {"hostname": "h2", "user": "u2", "name": "W", "operating_system": "windows", "polling_frequency": 3},
            "n3": {"hostname": "h3", "user": "u3", "name": "X", "operating_system": "other", "polling_frequency": 1},
        },
    )

    monkeypatch.setattr(drv, "PersistentConnection", lambda **kwargs: SimpleNamespace(**kwargs))
    monkeypatch.setattr(drv, "LinuxMetricsProvider", lambda conn: ("linux", conn))
    monkeypatch.setattr(drv, "WindowsMetricsProvider", lambda conn: ("windows", conn))

    nodes = load_targets(temp_config)
    assert len(nodes) == 2
    assert {n.name for n in nodes} == {"L", "W"}
    linux_node = next(n for n in nodes if n.name == "L")
    assert linux_node.polling_paused is True

    temp_config.decrypted_list = str((SimpleNamespace()).__class__)  # impossible path
    # Force missing file branch
    temp_config.decrypted_list = "/tmp/definitely_missing_zero_monitor_file.json"
    assert load_targets(temp_config) == []


def test_driver_remove_node_missing_and_error(fake_bus, temp_config, monkeypatch):
    _write_devices(temp_config.decrypted_list, {"k1": {"name": "A"}})
    d = Driver(fake_bus, temp_config)
    d.polling_agent = DummyPollingAgent(None)
    d.reload_config = lambda: fake_bus.publish("RELOAD", True)

    d.remove_node("missing")
    assert ("ACK_REMOVE_NODE", {"node": "missing", "success": False}) in fake_bus.published

    monkeypatch.setattr(drv, "load", lambda *_: (_ for _ in ()).throw(RuntimeError("bad json")))
    d.remove_node("A")
    assert ("ACK_REMOVE_NODE", {"node": "A", "success": False}) in fake_bus.published


def test_driver_add_duplicate_update_name_no_match_and_dispatch_edges(fake_bus, temp_config, monkeypatch):
    _write_devices(temp_config.decrypted_list, {"k1": {"name": "A", "hostname": "h", "user": "u", "operating_system": "linux"}})
    d = Driver(fake_bus, temp_config)
    d.polling_agent = DummyPollingAgent(None)
    d.reload_config = lambda: fake_bus.publish("RELOAD", True)

    d.add_node({"name": "A"})
    with open(temp_config.decrypted_list, "r", encoding="utf-8") as f:
        same = json.load(f)
    assert len(same) == 1

    d.update_device_name({"old_name": "missing", "new_name": "new"})
    assert not any(name == "ACK_UPDATE_DEVICE_NAME" for name, _ in fake_bus.published)

    class BoomQueue:
        def get(self, timeout=1):
            raise RuntimeError("timeout")

    d.metrics_queue = BoomQueue()
    calls = {"n": 0}
    d.running = True

    def publish_stop(name, payload):
        fake_bus.published.append((name, payload))

    d.event_bus.publish = publish_stop
    orig_continue = d._dispatch_metrics

    def fake_get(timeout=1):
        calls["n"] += 1
        d.running = False
        raise RuntimeError("timeout")

    d.metrics_queue.get = fake_get
    d._dispatch_metrics()

    d.running = True
    d.metrics_queue = SimpleNamespace(get=lambda timeout=1: "evt")
    d.event_bus.publish = lambda name, payload: setattr(d, "running", False)
    d._dispatch_metrics()


def test_driver_dispatch_breaks_before_publish_when_stopped(fake_bus, temp_config):
    d = Driver(fake_bus, temp_config)
    d.running = True

    def get_then_stop(timeout=1):
        d.running = False
        return "evt"

    d.metrics_queue = SimpleNamespace(get=get_then_stop)
    published = []
    d.event_bus.publish = lambda name, payload: published.append((name, payload))
    d._dispatch_metrics()
    assert published == []

