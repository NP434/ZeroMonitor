# Fake Event Bus and Metric Event classes for testing purposes. In a real implementation,
# these would be provided by the actual event system in use and would likely have more complex structures
# and behaviors.

import json
import os
import smtplib
import ssl
import logging
from email.message import EmailMessage
from typing import Optional
from event_bus import EventBus


# Data Interpreter Module
class DataInterpreter:
    # Default Thresholds for metrics (can be overridden per device)
    DEFAULT_THRESHOLDS = {
        "cpu_load_1m": 0.80,
        "mem_used_percent": 85.0,
        "disk_used_percent": 90.0,
        "cpu_temp_c": 80.0,
        "core_voltage_v": 1.30,
        "cpu_clock_mhz": 2200.0,
        "uptime_seconds": 1209600.0,
        "net_rx_kbps": 50000.0,
        "net_tx_kbps": 50000.0,
    }

    # Optional hysteresis margins (how far below threshold to clear alert)
    HYSTERESIS = {
        "cpu_load_1m": 0.05,          # 5% drop required to clear
        "mem_used_percent": 5.0,
        "disk_used_percent": 5.0,
        "cpu_temp_c": 5.0,
        "core_voltage_v": 0.05,
        "cpu_clock_mhz": 100.0,
        "uptime_seconds": 3600.0,
        "net_rx_kbps": 5000.0,
        "net_tx_kbps": 5000.0,
    }

    def __init__(
        self,
        event_bus: EventBus,
        config,
        json_filepath: str = "data/cache_data.json",
        smtp_server: Optional[str] = "smtp.gmail.com",
        smtp_port: Optional[int] = 465,
        smtp_user: Optional[str] = "zeromonitoralerts@gmail.com",
        smtp_password: Optional[str] = "xxdesmmolmmtdqdq",
        email_from: Optional[str] = "zeromonitoralerts@gmail.com",
        email_to: Optional[str] = "weeboo187@gmail.com",
    ):
        self.event_bus = event_bus
        self.config = config # For DEV MODE and Pathing

        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self.device_thresholds = {}

        # Tracks current alert state: {(node, metric): bool}
        self.alert_state = {}

        # Persistence and email config needs to be loaded from a config file.
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
        import logging
        logging.info(f"[DataInterpreter] Received METRIC_EVENT for node: {metric_event.node}, success: {metric_event.success}")

        if not metric_event.success:
            logging.warning(f"[DataInterpreter] Handling failed metric event for {metric_event.node}: {metric_event.payload}")
            try:
                offline_payload = self._build_offline_payload(metric_event)
                self._write_to_json_file(offline_payload)
                self.event_bus.publish("device_offline", offline_payload)
                self.event_bus.publish("data_interpreted", offline_payload)
            except Exception as e:
                logging.error(f"[DataInterpreter] Failed to write offline event: {e}")
            return

        interpreted = self.process_data(metric_event)

        # Annotate severities so they're always present in the published interpreted data
        interpreted = self._annotate_severity(interpreted)
        interpreted["status"] = "online"
        interpreted["success"] = True

        # Persist interpreted metrics to JSON file (updates per-node entry)
        try:
            self._write_to_json_file(interpreted)
        except Exception as e:
            # swallow persistence errors to not break pipeline
            print("JSON write error: ", e)

        # If any severity is 'warning', attempt to send an email alert
        try:
            if any(s in ["warning", "critical", "severe"] for s in interpreted.get("severities", {}).values()
                   if s is not None):
                self._send_warning_email(interpreted)
        except Exception as e:
            # swallow email errors
            print("Email error: ", e)

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
                "core_voltage_v": payload.get("core_voltage_v"),
                "cpu_clock_mhz": payload.get("cpu_clock_mhz"),
                "uptime_seconds": payload.get("uptime_seconds"),
                "net_rx_kbps": payload.get("net_rx_kbps"),
                "net_tx_kbps": payload.get("net_tx_kbps"),
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

    def _load_cache_entries(self):
        filepath = self.json_filepath
        if not os.path.exists(filepath):
            return {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _ensure_cache_directory(self):
        dirpath = os.path.dirname(self.json_filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

    def _write_cache_entries(self, data):
        filepath = self.json_filepath
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, filepath)

    def _build_offline_payload(self, metric_event):
        node = metric_event.node
        existing_entry = self._load_cache_entries().get(node, {})

        return {
            "node": node,
            "timestamp": metric_event.timestamp,
            "status": "offline",
            "success": False,
            "error": metric_event.payload.get("error", "SSH command failed"),
            "metrics": existing_entry.get("metrics", {}),
            "severities": existing_entry.get("severities", {}),
        }

    # Persistence: write/update JSON file with latest interpreted data per node
    def _write_to_json_file(self, interpreted):
        data = self._load_cache_entries()
        self._ensure_cache_directory()

        # Update node entry
        node = interpreted.get("node")
        if node is None:
            return

        stored_entry = dict(interpreted)
        if stored_entry.get("status") == "online":
            stored_entry.pop("error", None)

        data[node] = stored_entry
        self._write_cache_entries(data)

        import logging
        logging.info(f"[DataInterpreter] Updated cache_data.json for node '{node}' at {interpreted.get('timestamp')}")

    def _write_offline_event_to_json(self, metric_event):
        """Write offline status to cache when device fails SSH command"""
        offline_payload = self._build_offline_payload(metric_event)
        self._write_to_json_file(offline_payload)
        logging.info(f"[DataInterpreter] Marked device '{metric_event.node}' as OFFLINE at {metric_event.timestamp}")

    # Email sending for warnings (no-op if SMTP not configured)
    def _send_warning_email(self, interpreted):
        if not (self.smtp_server and self.smtp_port and self.email_from and self.email_to):
            # SMTP not configured: skip sending
            return

        try:
            import logging
            logging.info(f"[DataInterpreter] Attempting to send warning email for {interpreted.get('node')}")
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

            import logging
            logging.info(f"[DataInterpreter] Warning email sent successfully")
        except Exception as e:
            import logging
            logging.error(f"[DataInterpreter] Failed to send warning email: {e}")

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
