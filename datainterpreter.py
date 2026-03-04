
# Fake Event Bus and Metric Event classes for testing purposes. In a real implementation,
# these would be provided by the actual event system in use and would likely have more complex structures
# and behaviors.

import time
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional


class FakeEventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        self.subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event_type, data):
        # Single debug print (shows event type and payload once)
        print(f"Event Published: {event_type} → {data}")

        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)


class FakeMetricEvent:
    def __init__(self, node, payload):
        self.node = node
        self.payload = payload
        self.timestamp = time.ctime()
        self.success = True


# Data Interpreter Module
class DataInterpreter:
    # Default Thresholds for metrics (can be overridden per device)
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

    def __init__(
        self,
        event_bus,
        json_filepath: str = "data_output.json",
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        email_from: Optional[str] = None,
        email_to: Optional[str] = None,
    ):
        self.event_bus = event_bus
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self.device_thresholds = {}

        # Tracks current alert state: {(node, metric): bool}
        self.alert_state = {}

        # Persistence and email config
        self.json_filepath = json_filepath
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to

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

        # Persist interpreted metrics to JSON file (updates per-node entry)
        try:
            self._write_to_json_file(interpreted)
        except Exception:
            # swallow persistence errors to not break pipeline
            pass

        # If any severity is 'warning', attempt to send an email alert
        try:
            if any(s == "warning" or "critical" or "severe" for s in interpreted.get("severities", {}).values() if s is not None):
                self._send_warning_email(interpreted)
        except Exception:
            # swallow email errors
            pass

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

    # Persistence: write/update JSON file with latest interpreted data per node
    def _write_to_json_file(self, interpreted):
        data = {}
        filepath = self.json_filepath

        # Ensure directory exists
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        # Load existing
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        # Update node entry
        node = interpreted.get("node")
        if node is None:
            return

        # Store the interpreted dict (safe types) under node key
        data[node] = interpreted

        # Write back atomically
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, filepath)

    # Email Logic (need to find where to acquire the user's email address for the "to" field,
    # maybe in device_list.json or a separate config file? For now it's just env vars)
    '''
    # Email sending for warnings (no-op if SMTP not configured)
    def _send_warning_email(self, interpreted):
        if not (self.smtp_server and self.smtp_port and self.email_from and self.email_to):
            # SMTP not configured: skip sending
            return

        subject = f"Warning: metrics for {interpreted.get('node')}"
        body = json.dumps(interpreted, indent=2, sort_keys=True)

        msg = EmailMessage()
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        msg["Subject"] = subject
        msg.set_content(body)


        # Email sending with SSL/TLS if port is 465, otherwise starttls. Login if credentials provided.
        
        # Choose connection method
        context = ssl.create_default_context()
        if self.smtp_port == 465:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
    '''

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
