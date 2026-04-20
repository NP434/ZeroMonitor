from types import SimpleNamespace

from src import polling_agent as pa
from src.polling_agent import (
    LinuxMetricsProvider,
    MetricEvent,
    Node,
    PersistentConnection,
    PollingAgent,
    SystemMetrics,
    WindowsMetricsProvider,
    run_node,
)


class DummyStop:
    def __init__(self, first_set=False):
        self._set = first_set
        self.wait_calls = 0

    def is_set(self):
        return self._set

    def wait(self, _timeout):
        self.wait_calls += 1
        return self._set

    def set(self):
        self._set = True


class DummyConn:
    def __init__(self, stdout=""):
        self.stdout = stdout
        self.closed = False

    def run(self, *args, **kwargs):
        return SimpleNamespace(stdout=self.stdout)

    def close(self):
        self.closed = True


def test_linux_provider_collect_and_net_rate(monkeypatch):
    stdout = "\n".join(
        [
            "HOST=host1",
            "TEMP=50000",
            "LOAD=0.50",
            "MEM=200,100",
            "DISK=25%",
            "CLOCK=2000000",
            "VOLT=1.20",
            "UPTIME=123.4",
            "NET=1000,2000",
        ]
    )
    conn = DummyConn(stdout)
    p = LinuxMetricsProvider(conn)

    times = iter([10.0, 12.0])
    monkeypatch.setattr(pa.time, "monotonic", lambda: next(times))

    first = p.collect("node")
    assert first.hostname == "host1"
    assert first.cpu_temp_c == 50.0
    assert first.cpu_clock_mhz == 2000.0
    assert first.net_rx_kbps is None

    conn.stdout = stdout.replace("NET=1000,2000", "NET=3000,6000")
    second = p.collect("node")
    assert second.net_rx_kbps is not None
    assert second.net_tx_kbps is not None


def test_windows_provider_collect_parsing():
    stdout = "\n".join(
        [
            "HOST=WIN1",
            "CPU=30",
            "MEM=1000,200",
            "DISK=55",
            "CLOCK=2400",
            "UPTIME=200",
            "NET_RX_BPS=1000",
            "NET_TX_BPS=2000",
        ]
    )
    conn = DummyConn(stdout)
    p = WindowsMetricsProvider(conn)
    m = p.collect("node")

    assert m.hostname == "WIN1"
    assert m.cpu_load_1m == 0.3
    assert m.mem_used_mb == 800
    assert m.net_rx_kbps == 8.0


def test_persistent_connection_run_success_and_fail(monkeypatch):
    class FakeFabric:
        total_calls = 0

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.closed = False

        def run(self, *_args, **_kwargs):
            FakeFabric.total_calls += 1
            if FakeFabric.total_calls < 2:
                raise RuntimeError("retry")
            return "ok"

        def close(self):
            self.closed = True

    monkeypatch.setattr(pa, "Connection", lambda **kwargs: FakeFabric(**kwargs))
    monkeypatch.setattr(pa.time, "sleep", lambda *_: None)

    c = PersistentConnection("h", "u", "k", max_retries=2)
    out = c.run("echo", node_name="n")
    assert out == "ok"

    c2 = PersistentConnection("h", "u", "k", max_retries=1)

    class Stop:
        def wait(self, _):
            return True

    monkeypatch.setattr(pa, "Connection", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("x")))
    try:
        c2.run("echo", stop_event=Stop())
    except RuntimeError as e:
        assert "shutdown" in str(e)


def test_polling_agent_reconcile_and_helpers(monkeypatch):
    q = []
    agent = PollingAgent(q)

    added = []
    removed = []
    updated = []

    monkeypatch.setattr(agent, "add_node", lambda node: added.append(node.name))
    monkeypatch.setattr(agent, "remove_node", lambda name: removed.append(name))
    monkeypatch.setattr(agent, "update_node", lambda new_map, name: updated.append(name))

    n1 = Node("A", provider=SimpleNamespace(conn=DummyConn()), interval=1)
    n2 = Node("B", provider=SimpleNamespace(conn=DummyConn()), interval=1)
    agent.workers = {"A": (n1, None)}

    agent.reconcile([n1, n2])
    assert added == ["B"]
    assert updated == ["A"]


def test_polling_agent_add_remove_update_shutdown(monkeypatch):
    queue = []
    agent = PollingAgent(queue)

    class Exec:
        def __init__(self):
            self.submitted = []

        def submit(self, fn, *args):
            self.submitted.append((fn, args))
            return "future"

        def shutdown(self, wait=True, cancel_futures=True):
            self.was_shutdown = True

    agent.worker_executor = Exec()
    node = Node("N", provider=SimpleNamespace(conn=DummyConn()), interval=1)
    agent.add_node(node)
    assert "N" in agent.workers

    new = Node("N", provider=SimpleNamespace(conn=DummyConn()), interval=2)
    agent.update_node({"N": new}, "N")
    assert agent.workers["N"][0].interval == 2

    agent.remove_node("N")
    assert "N" not in agent.workers


def test_run_node_success_failure_and_pause(monkeypatch):
    metrics = SystemMetrics(
        hostname="h",
        timestamp="t",
        cpu_temp_c=1,
        cpu_load_1m=0.1,
        mem_total_mb=10,
        mem_used_mb=5,
        disk_used_percent=20,
        core_voltage_v=None,
        cpu_clock_mhz=None,
        uptime_seconds=None,
        net_rx_kbps=None,
        net_tx_kbps=None,
    )

    class Provider:
        def __init__(self):
            self.conn = DummyConn()
            self.calls = 0

        def collect(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("fail")
            return metrics

    class Q:
        def __init__(self):
            self.items = []

        def put(self, item):
            self.items.append(item)

    stop = DummyStop(False)

    calls = {"n": 0}

    def is_set_seq():
        calls["n"] += 1
        return calls["n"] > 3

    stop.is_set = is_set_seq
    stop.wait = lambda _t: False

    node = Node("N", provider=Provider(), interval=0, stop_event=stop)
    q = Q()
    monkeypatch.setattr(pa.time, "monotonic", lambda: 0)

    run_node(node, q)

    assert any(isinstance(i, MetricEvent) and i.success for i in q.items)
    assert any(isinstance(i, MetricEvent) and not i.success for i in q.items)
    assert node.provider.conn.closed is True

    # paused branch
    stop2 = DummyStop(False)
    seq = {"n": 0}
    stop2.is_set = lambda: (seq.__setitem__("n", seq["n"] + 1) or False) if seq["n"] < 2 else True
    stop2.wait = lambda _t: False

    node2 = Node("P", provider=Provider(), interval=0, stop_event=stop2, polling_paused=True)
    q2 = Q()
    run_node(node2, q2)
    assert q2.items == []


def test_metrics_provider_collect_base_method_returns_none():
    assert pa.MetricsProvider.collect(object(), "node") is None


def test_linux_and_windows_provider_parse_fallbacks(monkeypatch):
    linux_stdout = "\n".join([
        "HOST=host1",
        "TEMP=bad",
        "LOAD=0.50",
        "MEM=200,100",
        "DISK=25%",
        "CLOCK=oops",
        "VOLT=bad",
        "UPTIME=bad",
        "NET=bad,bad",
    ])
    lp = LinuxMetricsProvider(DummyConn(linux_stdout))
    monkeypatch.setattr(pa.time, "monotonic", lambda: 1.0)
    m = lp.collect("node")
    assert m.cpu_temp_c is None
    assert m.cpu_clock_mhz is None
    assert m.core_voltage_v is None
    assert m.uptime_seconds is None
    assert m.net_rx_kbps is None

    windows_stdout = "\n".join([
        "HOST=WIN1",
        "CPU=30",
        "MEM=1000,200",
        "DISK=55",
        "CLOCK=bad",
        "UPTIME=bad",
        "NET_RX_BPS=bad",
        "NET_TX_BPS=bad",
    ])
    wp = WindowsMetricsProvider(DummyConn(windows_stdout))
    m2 = wp.collect("node")
    assert m2.cpu_clock_mhz is None
    assert m2.uptime_seconds is None
    assert m2.net_rx_kbps is None
    assert m2.net_tx_kbps is None


def test_persistent_connection_exhaustion_and_close_paths(monkeypatch):
    class FailFabric:
        def __init__(self, **kwargs):
            pass

        def run(self, *_args, **_kwargs):
            raise RuntimeError("always bad")

        def close(self):
            raise RuntimeError("close bad")

    monkeypatch.setattr(pa, "Connection", lambda **kwargs: FailFabric(**kwargs))
    monkeypatch.setattr(pa.time, "sleep", lambda *_: None)

    conn = PersistentConnection("h", "u", "k", max_retries=1)
    try:
        conn.run("echo", node_name="n")
    except RuntimeError as e:
        assert "failed after 1 retries" in str(e)

    conn.conn = FailFabric()
    conn.close()
    assert conn.conn is None


def test_polling_agent_launch_reconcile_remove_none_and_shutdown(monkeypatch):
    queue = []
    agent = PollingAgent(queue)

    launched = []
    monkeypatch.setattr(agent, "reconcile", lambda nodes: launched.extend(nodes))
    agent.launch_nodes(["a", "b"])
    assert launched == ["a", "b"]

    agent2 = PollingAgent(queue)
    agent2.workers = {"old": (Node("old", provider=SimpleNamespace(conn=DummyConn()), interval=1, stop_event=DummyStop()), None)}
    removed = []
    monkeypatch.setattr(agent2, "remove_node", lambda name: removed.append(name))
    monkeypatch.setattr(agent2, "update_node", lambda *_: None)
    monkeypatch.setattr(agent2, "add_node", lambda *_: None)
    agent2.reconcile([])
    assert removed == ["old"]

    # remove missing branch
    real_agent = PollingAgent(queue)
    real_agent.remove_node("missing")

    called = []
    real_agent.workers = {
        "a": (Node("a", provider=SimpleNamespace(conn=DummyConn()), interval=1, stop_event=DummyStop()), None),
        "b": (Node("b", provider=SimpleNamespace(conn=DummyConn()), interval=1, stop_event=DummyStop()), None),
    }
    monkeypatch.setattr(real_agent, "remove_node", lambda name: called.append(name))
    real_agent.stop_all_nodes()
    assert called == ["a", "b"]

    class Exec:
        def __init__(self):
            self.args = None
        def shutdown(self, wait=True, cancel_futures=True):
            self.args = (wait, cancel_futures)
    real_agent.worker_executor = Exec()
    monkeypatch.setattr(real_agent, "stop_all_nodes", lambda: called.append("stopped"))
    real_agent.shutdown()
    assert "stopped" in called
    assert real_agent.worker_executor.args == (True, True)


def test_run_node_stop_during_wait_and_time_drift(monkeypatch):
    class Provider:
        def __init__(self):
            self.conn = DummyConn()
        def collect(self, *_args, **_kwargs):
            return SystemMetrics("h", "t", 1, 0.1, 1, 1, 1, None, None, None, None, None)

    class Q:
        def __init__(self):
            self.items = []
        def put(self, item):
            self.items.append(item)

    # stop during wait branch
    stop = DummyStop(False)
    stop.is_set = lambda: False
    stop.wait = lambda _t: True
    node = Node("N", provider=Provider(), interval=5, stop_event=stop)
    times_wait = iter([10, 0])
    monkeypatch.setattr(pa.time, "monotonic", lambda: next(times_wait))
    q = Q()
    run_node(node, q)
    assert q.items == []

    # timing drift reset branch + conn.close exception branch
    class BadCloseConn(DummyConn):
        def close(self):
            raise RuntimeError("no close")

    class SlowProvider:
        def __init__(self):
            self.conn = BadCloseConn()
            self.calls = 0
        def collect(self, *_args, **_kwargs):
            self.calls += 1
            return SystemMetrics("h", "t", 1, 0.1, 1, 1, 1, None, None, None, None, None)

    stop2 = DummyStop(False)
    seq = iter([False, False, True])
    stop2.is_set = lambda: next(seq)
    stop2.wait = lambda _t: False
    node2 = Node("S", provider=SlowProvider(), interval=0, stop_event=stop2)
    times = iter([0, 0, 5, 5, 5, 5, 5, 5])
    monkeypatch.setattr(pa.time, "monotonic", lambda: next(times))
    run_node(node2, Q())


def test_persistent_connection_open_password_branch(monkeypatch):
    created = {}

    class FakeFabric:
        def __init__(self, **kwargs):
            created.update(kwargs)

        def close(self):
            pass

    monkeypatch.setattr(pa, "Connection", lambda **kwargs: FakeFabric(**kwargs))

    conn = PersistentConnection("host", "user", "key.pem", password="secret")
    conn.open()

    assert conn.conn is not None
    assert created["host"] == "host"
    assert created["user"] == "user"

