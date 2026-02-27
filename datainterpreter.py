import time

class FakeEventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        self.subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event_type, data):
        print(f"Event Published: {event_type} → {event_type}: {data}")
        print(data)

        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)



class FakeMetricEvent:
    def __init__(self, node, payload):
        self.node = node
        self.payload = payload
        self.timestamp = time.time()
        self.success = True

class DataInterpreter:
    DEFAULT_THRESHOLDS = {
        "cpu_load_1m": 0.80,
        "mem_used_percent": 85.0,
        "disk_used_percent": 90.0,
        "cpu_temp_c": 80.0,
    }

    # Optional hysteresis margins (how far below threshold to clear alert)
    HYSTERESIS = {
        "cpu_load_1m": 0.05,          # 5% drop required to clear
        "mem_used_percent": 5.0,
        "disk_used_percent": 5.0,
        "cpu_temp_c": 5.0,
    }

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self.device_thresholds = {}

        # Tracks current alert state: {(node, metric): bool}
        self.alert_state = {}

        self.event_bus.subscribe("METRIC_EVENT", self.interpret_data)

    # Threshold Configuration
    def set_threshold(self, metric_name: str, threshold_value: float):
        self.thresholds[metric_name] = threshold_value

    def set_thresholds_for_device(self, device_name: str, thresholds: dict):
        self.device_thresholds.setdefault(device_name, {}).update(thresholds)

    def _get_thresholds_for_node(self, node_name):
        return {
            **self.thresholds,
            **self.device_thresholds.get(node_name, {})
        }

    # Main Entry Point
    def interpret_data(self, metric_event):
        if not metric_event.success:
            return

        interpreted = self.process_data(metric_event)

        # Annotate severities so they're always present in the published interpreted data
        interpreted = self._annotate_severity(interpreted)

        # Publish interpreted metrics (now always includes a 'severities' map)
        self.event_bus.publish("data_interpreted", interpreted)

        # Evaluate alerts using interpreted metrics
        triggered, cleared = self.check_thresholds(interpreted)

        if triggered:
            self.event_bus.publish("threshold_alert", {
                "node": interpreted["node"],
                "alerts": triggered,
                "timestamp": interpreted["timestamp"]
            })

        if cleared:
            self.event_bus.publish("threshold_cleared", {
                "node": interpreted["node"],
                "cleared": cleared,
                "timestamp": interpreted["timestamp"]
            })

    # Data Processing
    def process_data(self, metric_event):
        payload = metric_event.payload

        mem_used_percent = None
        if payload.get("mem_total_mb", 0) > 0:
            mem_used_percent = (
                payload.get("mem_used_mb", 0) / payload["mem_total_mb"]
            ) * 100

        return {
            "node": metric_event.node,
            "timestamp": metric_event.timestamp,
            "metrics": {
                "cpu_load_1m": payload.get("cpu_load_1m"),
                "cpu_temp_c": payload.get("cpu_temp_c"),
                "mem_used_percent": mem_used_percent,
                "disk_used_percent": payload.get("disk_used_percent"),
                "mem_used_mb": payload.get("mem_used_mb"),
                "mem_total_mb": payload.get("mem_total_mb"),
            }
        }

    # Annotate per-metric severities. Always produces a 'severities' dict
    def _annotate_severity(self, interpreted):
        node = interpreted.get("node")
        metrics = interpreted.get("metrics", {})
        thresholds = self._get_thresholds_for_node(node)

        severities = {}
        for metric, value in metrics.items():
            # Default severity is 'normal' when we have a numeric value
            if value is None:
                severities[metric] = None
                continue

            threshold = thresholds.get(metric)
            if threshold is None:
                # No threshold configured -> normal
                severities[metric] = "normal"
                continue

            # If value exceeds threshold compute severity, else 'normal'
            if value > threshold:
                severities[metric] = self._calculate_severity(value, threshold)
            else:
                severities[metric] = "normal"

        # attach severities map without changing existing metrics structure
        interpreted["severities"] = severities
        return interpreted

    # Alert Evaluation
    def check_thresholds(self, interpreted):
        node = interpreted["node"]
        metrics = interpreted["metrics"]
        thresholds = self._get_thresholds_for_node(node)

        triggered_alerts = []
        cleared_alerts = []

        for metric, threshold in thresholds.items():
            value = metrics.get(metric)
            if value is None:
                continue

            key = (node, metric)

            # Current vs previous state
            was_alerting = self.alert_state.get(key, False)
            is_alerting = value > threshold

            # Hysteresis logic for clearing
            hysteresis = self.HYSTERESIS.get(metric, 0)
            clear_threshold = threshold - hysteresis

            if was_alerting:
                if value < clear_threshold:
                    # CLEAR event
                    cleared_alerts.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold
                    })
                    self.alert_state[key] = False
            else:
                if is_alerting:
                    # TRIGGER event
                    triggered_alerts.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "severity": self._calculate_severity(value, threshold)
                    })
                    self.alert_state[key] = True

        return triggered_alerts, cleared_alerts

    # Severity Calculation
    def _calculate_severity(self, value, threshold):
        if threshold == 0:
            return "warning"

        delta_ratio = (value - threshold) / threshold

        if delta_ratio < 0.10:
            return "warning"
        elif delta_ratio < 0.25:
            return "critical"
        else:
            return "severe"


event = FakeEventBus()
interpreter = DataInterpreter(event)

event.publish("METRIC_EVENT", FakeMetricEvent(
    node="server-1",
    payload={
        "cpu_load_1m": 0.85,
        "mem_used_mb": 4000,
        "mem_total_mb": 8000,
        "disk_used_percent": 50.0,
        "cpu_temp_c": 60.0
    }
))


event.publish("METRIC_EVENT", FakeMetricEvent(
    node="server-2",
    payload={
        "cpu_load_1m": 0.6,   # below threshold AND hysteresis
        "cpu_temp_c": 70,
        "mem_used_mb": 3000,
        "mem_total_mb": 8000,
        "disk_used_percent": 60,
    }
))
