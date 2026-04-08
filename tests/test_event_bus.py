import time

from event_bus import EventBus


def test_event_bus_publish_subscribe_and_stop():
    bus = EventBus()
    received = []

    bus.subscribe("X", lambda payload: received.append(payload))
    bus.start()
    bus.publish("X", {"ok": True})

    for _ in range(20):
        if received:
            break
        time.sleep(0.01)

    bus.stop()
    assert received == [{"ok": True}]


def test_event_bus_handler_exception_does_not_crash(monkeypatch):
    bus = EventBus()
    printed = []

    def bad(_):
        raise RuntimeError("boom")

    bus.subscribe("X", bad)
    monkeypatch.setattr("builtins.print", lambda msg: printed.append(msg))

    bus.start()
    bus.publish("X", 1)

    for _ in range(20):
        if printed:
            break
        time.sleep(0.01)

    bus.stop()
    assert any("Handler error" in p for p in printed)

