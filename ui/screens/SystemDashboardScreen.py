import datetime
import pygame
import json
import os
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.Dropdown import DropDown
import ui.theme as theme
import ui.utilities as utilities


class SystemDashboardScreen(BaseScreen):
    """
    System-wide dashboard showing overall status and aggregated metrics
    """

    METRIC_LABELS = {
        "cpu_load_1m": "CPU Load (1m)",
        "cpu_temp_c": "CPU Temp",
        "mem_used_percent": "Memory",
        "disk_used_percent": "Disk",
        "net_rx_kbps": "Download",
        "net_tx_kbps": "Upload",
    }

    METRIC_UNITS = {
        "cpu_load_1m": "",
        "cpu_temp_c": "°C",
        "mem_used_percent": "%",
        "disk_used_percent": "%",
        "net_rx_kbps": "",
        "net_tx_kbps": "",
    }

    GRAPH_SCALE_LIMITS = {
        "cpu_load_1m": 1.0,
        "cpu_temp_c": 100.0,
        "mem_used_percent": 100.0,
        "disk_used_percent": 100.0,
        "net_rx_kbps": 50000.0,
        "net_tx_kbps": 50000.0,
    }

    GRAPH_METRICS = [
        "cpu_load_1m",
        "cpu_temp_c",
        "mem_used_percent",
        "disk_used_percent",
        "net_rx_kbps",
        "net_tx_kbps",
    ]

    DEFAULT_GRAPH_METRICS = [
        "cpu_load_1m",
        "cpu_temp_c",
        "mem_used_percent",
        "disk_used_percent",
    ]

    NETWORK_GRAPH_METRICS = [
        "net_rx_kbps",
        "net_tx_kbps",
    ]

    GRAPH_COLORS = {
        "cpu_load_1m": theme.BRIGHT_BLUE,
        "cpu_temp_c": theme.RED,
        "mem_used_percent": theme.YELLOW,
        "disk_used_percent": theme.ORANGE,
        "net_rx_kbps": theme.GREEN,
        "net_tx_kbps": theme.PURPLE,
    }

    GRAPH_SHORT_LABELS = {
        "cpu_load_1m": "CPU",
        "cpu_temp_c": "Temp",
        "mem_used_percent": "Mem",
        "disk_used_percent": "Disk",
        "net_rx_kbps": "Down",
        "net_tx_kbps": "Up",
    }

    HISTORY_LIMIT = 30

    def __init__(self, app):
        super().__init__(app)

        # Load assets
        self.load_assets()
        power_icon_surface = self.assets.get("power_button.png")
        if power_icon_surface is None:
            # Reuse the same icon source MainScreen uses.
            shared_power_path = os.path.join("assets", "main", "power_button.png")
            if os.path.exists(shared_power_path):
                power_icon_surface = pygame.image.load(shared_power_path).convert_alpha()
            else:
                power_icon_surface = pygame.Surface((40, 40), pygame.SRCALPHA)

        power_icon = pygame.transform.smoothscale(power_icon_surface, (40, 40))

        # Create Power Button (match MainScreen sizing/placement)
        power_width = 50
        power_height = 50
        power_x = self.app.width - power_width - theme.MARGIN_XLARGE
        power_y = theme.MARGIN_LARGE + 5
        self.power_button = Button(
            rect=(power_x, power_y, power_width, power_height),
            image=power_icon,
            bg_color=theme.POWER_RED
        )

        # Create Main Screen Button (to go to device selection)
        main_btn_width = 140
        main_btn_height = 50
        main_btn_x = power_x - main_btn_width - theme.GAP_LARGE
        main_btn_y = theme.MARGIN_LARGE + 5
        self.main_screen_button = Button(
            rect=(main_btn_x, main_btn_y, main_btn_width, main_btn_height),
            bg_color=theme.BLUE,
            text="Devices"
        )

        # Cache data
        self.cache_data = {}
        self.metric_history = []
        self._last_history_key = None
        self.show_network_lines = False
        self.network_toggle_button = Button(
            rect=(0, 0, 120, 30),
            text="Show Net",
            bg_color=(45, 45, 45),
            font=theme.FONT_SMALL,
        )
        self._load_cache_data()
        self.selected_graph_device = None
        self.device_selector = DropDown(
            self.app,
            pygame.Rect(0, 0, 180, 28),
            ["No devices"],
            default="No devices",
        )
        self._refresh_graph_device_selector()

        # Subscribe to data updates for real-time refresh
        self.app.bus.subscribe("data_interpreted", self._on_data_interpreted)

    def _load_cache_data(self):
        """Load cache data from cache_data.json"""
        cache_filepath = getattr(self.app.config, "cache_file", "data/cache_data.json")
        if os.path.exists(cache_filepath):
            try:
                with open(cache_filepath, 'r') as f:
                    self.cache_data = json.load(f)
            except Exception as e:
                print(f"Error loading cache_data.json: {e}")
                self.cache_data = {}

    def _get_device_status(self, device_name):
        """Get device status from cache data"""
        if device_name not in self.cache_data:
            return "Offline"

        device_data = self.cache_data.get(device_name, {})

        # Check if device has explicit offline status
        if device_data.get("status") == "offline":
            return "Offline"

        # Check if device has a success flag
        if not device_data.get("success", True):
            return "Offline"

        # If device has metrics, it's online
        if device_data.get("metrics"):
            return "Online"

        return "Offline"

    def _calculate_aggregated_metrics(self):
        """Calculate average metrics across all devices"""
        if not self.cache_data:
            return None

        aggregated = {
            "cpu_load_1m": [],
            "cpu_temp_c": [],
            "mem_used_percent": [],
            "disk_used_percent": [],
            "net_rx_kbps": [],
            "net_tx_kbps": [],
        }

        for device_name, device_data in self.cache_data.items():
            metrics = device_data.get("metrics", {})
            for key in aggregated.keys():
                if key in metrics and metrics[key] is not None:
                    aggregated[key].append(metrics[key])

        # Calculate averages
        averages = {}
        for metric, values in aggregated.items():
            if values:
                averages[metric] = sum(values) / len(values)
            else:
                averages[metric] = None

        return averages

    def _get_device_counts(self):
        """Get device connection status counts"""
        total = len(self.app.devices)
        online = sum(1 for device in self.app.devices if self._get_device_status(device.get("name")) == "Online")
        offline = total - online

        return total, online, offline

    def _get_history_key(self):
        if not self.cache_data or not self.selected_graph_device:
            return None

        device_data = self.cache_data.get(self.selected_graph_device)
        if not isinstance(device_data, dict):
            return None

        return (
            self.selected_graph_device,
            device_data.get("timestamp"),
            device_data.get("status"),
            device_data.get("success"),
        )

    def _refresh_graph_device_selector(self):
        device_names = [d.get("name") for d in self.app.devices if d.get("name")]
        cache_names = [name for name in self.cache_data.keys() if name]

        ordered = []
        seen = set()
        for name in device_names + cache_names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)

        options = ordered or ["No devices"]
        self.device_selector.options = options

        if ordered:
            if self.selected_graph_device not in ordered:
                self.selected_graph_device = ordered[0]
                self.metric_history = []
                self._last_history_key = None
            self.device_selector.selected = self.selected_graph_device
        else:
            self.selected_graph_device = None
            self.device_selector.selected = "No devices"
            self.metric_history = []
            self._last_history_key = None

    def _get_selected_graph_metrics(self):
        if not self.selected_graph_device:
            return None

        device_data = self.cache_data.get(self.selected_graph_device, {})
        if not isinstance(device_data, dict):
            return None

        metrics = device_data.get("metrics", {})
        if not isinstance(metrics, dict):
            return None
        return metrics

    def _record_metric_history(self, averages):
        _ = averages
        history_key = self._get_history_key()
        if not history_key or history_key == self._last_history_key:
            return

        if not self.selected_graph_device:
            return

        device_data = self.cache_data.get(self.selected_graph_device, {})
        if not isinstance(device_data, dict):
            return

        selected_metrics = device_data.get("metrics", {})
        if not isinstance(selected_metrics, dict) or not selected_metrics:
            return

        latest_timestamp = device_data.get("timestamp")

        history_entry = {
            "timestamp": latest_timestamp,
            "metrics": {
                metric_key: selected_metrics.get(metric_key)
                for metric_key in self.GRAPH_METRICS
            },
        }

        self.metric_history.append(history_entry)
        if len(self.metric_history) > self.HISTORY_LIMIT:
            self.metric_history = self.metric_history[-self.HISTORY_LIMIT:]

        self._last_history_key = history_key

    def handle_event(self, event):
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.FINGERDOWN:
                pos = (
                    int(event.x * self.app.width),
                    int(event.y * self.app.height)
                )
            else:
                pos = event.pos

            selected = self.device_selector.handle_event(event)
            if selected in self.device_selector.options and selected != "No devices":
                if selected != self.selected_graph_device:
                    self.selected_graph_device = selected
                    self.metric_history = []
                    self._last_history_key = None

            selector_hit = self.device_selector.rect.collidepoint(pos)
            expanded_hit = False
            if self.device_selector.expanded:
                expanded_hit = self.device_selector._expanded_rect().collidepoint(pos)
            if selector_hit or expanded_hit:
                return

            # Power Button clicked
            if self.power_button.is_clicked(pos):
                self.app.ui_control.stop_system()

            # Main Screen Button clicked
            if self.main_screen_button.is_clicked(pos):
                self.app.change_screen("main")

            if self.network_toggle_button.is_clicked(pos):
                self.show_network_lines = not self.show_network_lines
                self.network_toggle_button.text = "Hide Net" if self.show_network_lines else "Show Net"

    def update(self):
        self._load_cache_data()
        self._refresh_graph_device_selector()
        averages = self._calculate_aggregated_metrics()
        if averages:
            self._record_metric_history(averages)

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Draw top bar background
        pygame.draw.rect(surface, theme.TOPBAR_BG, (0, 0, self.app.width, theme.TOPBAR_HEIGHT))
        pygame.draw.line(surface, theme.TOPBAR_BORDER_COLOR, (0, theme.TOPBAR_HEIGHT),
                        (self.app.width, theme.TOPBAR_HEIGHT), theme.TOPBAR_BORDER_WIDTH)

        # Time (topleft)
        now = datetime.datetime.now().strftime("%H:%M")
        time_text = theme.FONT_MEDIUM.render(now, True, theme.BRIGHT_BLUE)
        surface.blit(time_text, (theme.MARGIN_XLARGE, theme.MARGIN_LARGE + 5))

        # Title Centered
        title_text = theme.FONT_TITLE.render("System Overview", True, theme.BRIGHT_BLUE)
        title_rect = title_text.get_rect(center=(self.app.width // 2, theme.TOPBAR_HEIGHT // 2 + 5))
        surface.blit(title_text, title_rect)

        # Draw buttons
        self.main_screen_button.draw(surface)
        self.power_button.draw(surface)

        # Get device counts
        total, online, offline = self._get_device_counts()

        # Draw Device Status Section with title
        status_section_y = theme.TOPBAR_HEIGHT + theme.MARGIN_XLARGE
        status_x = theme.MARGIN_XLARGE
        content_width = self.app.width - (status_x * 2)
        content_center_x = status_x + (content_width // 2)

        status_title_text = theme.FONT_LARGE.render("Device Status", True, theme.BRIGHT_BLUE)
        status_title_rect = status_title_text.get_rect(center=(content_center_x, status_section_y + 14))
        surface.blit(status_title_text, status_title_rect)

        # Device count boxes in a row - fill available width for better readability
        box_y = status_section_y + 44
        content_width = self.app.width - (status_x * 2)
        box_gap = 20
        box_width = (content_width - (box_gap * 2)) // 3
        box_height = 92

        # Total Devices Box
        self._draw_status_box(surface, status_x, box_y, box_width, box_height, "Total", str(total), theme.BRIGHT_BLUE)

        # Online Devices Box
        self._draw_status_box(surface, status_x + box_width + box_gap, box_y, box_width, box_height, "Online", str(online), theme.GREEN)

        # Offline Devices Box
        self._draw_status_box(surface, status_x + ((box_width + box_gap) * 2), box_y, box_width, box_height, "Offline", str(offline), theme.RED)

        # Draw Selected Device Metrics + Graph Section
        metrics_section_y = box_y + box_height + theme.MARGIN_LARGE
        metrics_title = theme.FONT_LARGE.render("Selected Device Metrics", True, theme.BRIGHT_BLUE)
        metrics_title_rect = metrics_title.get_rect(center=(content_center_x, metrics_section_y + 14))
        surface.blit(metrics_title, metrics_title_rect)

        # Keep averages for dashboard-level availability checks/history updates.
        averages = self._calculate_aggregated_metrics()

        if averages:
            panel_top = metrics_section_y + 40
            panel_height = self.app.height - panel_top - theme.MARGIN_LARGE
            gap = theme.GAP_LARGE
            table_width = int(content_width * 0.40)
            graph_width = content_width - table_width - gap

            table_rect = pygame.Rect(status_x, panel_top, table_width, panel_height)
            graph_rect = pygame.Rect(table_rect.right + gap, panel_top, graph_width, panel_height)

            selected_metrics = self._get_selected_graph_metrics() or {}
            graph_metrics = self._get_active_graph_metrics(selected_metrics)
            self._draw_metrics_table(surface, table_rect, selected_metrics, graph_metrics)
            self._draw_metrics_graph(surface, graph_rect, selected_metrics, graph_metrics)
        else:
            no_data_font = theme.FONT_MEDIUM
            no_data_text = no_data_font.render("No device data available", True, theme.LIGHT_GRAY)
            surface.blit(no_data_text, (status_x, metrics_section_y + 45))

    def _draw_status_box(self, surface, x, y, width, height, label, value, color):
        """Draw a status box with label and value"""
        # Background box
        pygame.draw.rect(surface, theme.CARD_BG, (x, y, width, height), border_radius=theme.CARD_CORNER_RADIUS)
        # Border with glow effect
        pygame.draw.rect(surface, color, (x, y, width, height), theme.CARD_BORDER_WIDTH, border_radius=theme.CARD_CORNER_RADIUS)

        # Label with better spacing
        label_font = pygame.font.SysFont("Arial", 14)
        label_text = label_font.render(label, True, theme.LIGHTER_GRAY)
        surface.blit(label_text, (x + theme.CARD_PADDING, y + theme.PADDING_MEDIUM))

        # Value - larger and more prominent
        value_font = pygame.font.SysFont("Arial", 42, bold=True)
        value_text = value_font.render(value, True, color)
        value_rect = value_text.get_rect(center=(x + width // 2, y + height // 2 + 8))
        surface.blit(value_text, value_rect)

    def _draw_metrics_table(self, surface, rect, selected_metrics, graph_metrics):
        """Draw selected-device metrics with better formatting."""
        pygame.draw.rect(surface, theme.CARD_BG, rect, border_radius=theme.CARD_CORNER_RADIUS)
        pygame.draw.rect(surface, theme.BLUE, rect, theme.CARD_BORDER_WIDTH, border_radius=theme.CARD_CORNER_RADIUS)

        title_text = theme.FONT_MEDIUM.render("Device Metrics", True, theme.WHITE)
        surface.blit(title_text, (rect.x + theme.CARD_PADDING, rect.y + theme.CARD_PADDING))

        selected_name = self.selected_graph_device or "No device"
        selected_name_text = theme.FONT_SMALL.render(selected_name, True, theme.LIGHTER_GRAY)
        surface.blit(selected_name_text, (rect.x + theme.CARD_PADDING, rect.y + theme.CARD_PADDING + 22))

        legend_lane_width = 116
        lane_gap = 10
        metrics_rect = pygame.Rect(
            rect.x + theme.CARD_PADDING,
            rect.y + 54,
            max(120, rect.width - legend_lane_width - lane_gap - (theme.CARD_PADDING * 2)),
            rect.height - 62,
        )
        legend_rect = pygame.Rect(
            metrics_rect.right + lane_gap,
            rect.y + 58,
            max(96, rect.right - theme.CARD_PADDING - (metrics_rect.right + lane_gap)),
            rect.height - 68,
        )

        visible_metrics = [
            metric_key for metric_key in self.METRIC_LABELS
            if selected_metrics.get(metric_key) is not None
        ]

        if not self.selected_graph_device:
            empty_text = theme.FONT_SMALL.render("No device selected", True, theme.LIGHT_GRAY)
            surface.blit(empty_text, (metrics_rect.x, metrics_rect.y + 4))
            self._draw_averages_color_key(surface, legend_rect, graph_metrics)
            return

        if not visible_metrics:
            empty_text = theme.FONT_SMALL.render("No metrics for selected device", True, theme.LIGHT_GRAY)
            surface.blit(empty_text, (metrics_rect.x, metrics_rect.y + 4))
            self._draw_averages_color_key(surface, legend_rect, graph_metrics)
            return

        available_rows_height = max(120, metrics_rect.height - 8)
        row_height = max(28, min(40, available_rows_height // max(1, len(visible_metrics))))
        col_label_width = max(96, int(metrics_rect.width * 0.58))

        label_font = pygame.font.SysFont("Arial", 16)
        value_font = pygame.font.SysFont("Arial", 15, bold=True)

        current_y = metrics_rect.y + 2
        displayed = 0

        for metric_key, metric_label in self.METRIC_LABELS.items():
            if metric_key not in selected_metrics or selected_metrics[metric_key] is None:
                continue

            if current_y + row_height > metrics_rect.bottom:
                break

            # Alternate background for readability
            if displayed % 2 == 0:
                row_bg = (35, 35, 35)
                pygame.draw.rect(
                    surface,
                    row_bg,
                    (
                        rect.x + theme.PADDING_MEDIUM,
                        current_y - 6,
                        metrics_rect.width,
                        row_height,
                    ),
                    border_radius=8,
                )

            # Draw label
            label_text = label_font.render(metric_label, True, theme.LIGHT_GRAY)
            surface.blit(label_text, (metrics_rect.x, current_y))

            # Format value
            value = selected_metrics[metric_key]
            value_str = utilities.format_metric_value(metric_key, value)

            # Draw value with accent color
            value_text = value_font.render(value_str, True, theme.WHITE)
            value_x = metrics_rect.x + col_label_width
            surface.blit(value_text, (value_x, current_y))

            current_y += row_height
            displayed += 1

        self._draw_averages_color_key(surface, legend_rect, graph_metrics)

    def _draw_metrics_graph(self, surface, rect, selected_metrics, graph_metrics):
        """Draw a right-side live line graph for averaged metrics."""
        pygame.draw.rect(surface, theme.CARD_BG, rect, border_radius=theme.CARD_CORNER_RADIUS)
        pygame.draw.rect(surface, theme.BLUE, rect, theme.CARD_BORDER_WIDTH, border_radius=theme.CARD_CORNER_RADIUS)

        title_text = theme.FONT_MEDIUM.render("Live Trends", True, theme.WHITE)
        subtitle_text = theme.FONT_SMALL.render("Normalized", True, theme.LIGHTER_GRAY)
        surface.blit(title_text, (rect.x + theme.CARD_PADDING, rect.y + theme.CARD_PADDING))
        subtitle_rect = subtitle_text.get_rect(topright=(rect.right - theme.CARD_PADDING, rect.y + theme.CARD_PADDING + 2))
        surface.blit(subtitle_text, subtitle_rect)

        controls_top = rect.y + 36
        toggle_width = 104
        toggle_height = 26
        self.network_toggle_button.rect = pygame.Rect(
            rect.right - toggle_width - theme.CARD_PADDING,
            controls_top,
            toggle_width,
            toggle_height,
        )
        self.network_toggle_button.text = "Hide Net" if self.show_network_lines else "Show Net"
        self.network_toggle_button.bg_color = theme.BLUE if self.show_network_lines else (55, 55, 55)
        self.network_toggle_button.draw(surface)

        selector_width = max(132, min(176, rect.width - (theme.CARD_PADDING * 2) - 10))
        selector_y = controls_top + 16
        max_selector_y = rect.bottom - 36
        selector_y = min(selector_y, max_selector_y)

        device_label_y = selector_y - 16
        if device_label_y > rect.y + theme.CARD_PADDING + 2:
            device_label = theme.FONT_SMALL.render("Device", True, theme.LIGHTER_GRAY)
            surface.blit(device_label, (rect.x + theme.CARD_PADDING, device_label_y))

        self.device_selector.rect = pygame.Rect(
            rect.x + theme.CARD_PADDING,
            selector_y,
            selector_width,
            30,
        )
        self.device_selector.draw(surface)

        if self.device_selector.expanded:
            self.device_selector.draw_expanded(surface)

        if not self.selected_graph_device:
            no_selection_text = theme.FONT_MEDIUM.render("No device selected", True, theme.LIGHT_GRAY)
            no_selection_rect = no_selection_text.get_rect(center=rect.center)
            surface.blit(no_selection_text, no_selection_rect)
            return

        if not graph_metrics or len(self.metric_history) < 2:
            no_data_text = theme.FONT_MEDIUM.render("Waiting for more data...", True, theme.LIGHT_GRAY)
            no_data_rect = no_data_text.get_rect(center=rect.center)
            surface.blit(no_data_text, no_data_rect)
            return

        controls_bottom = max(self.network_toggle_button.rect.bottom, self.device_selector.rect.bottom)
        bottom_reserved = 44 if not self.show_network_lines else 26
        chart_top = min(controls_bottom + 10, rect.bottom - 48)
        chart_rect = pygame.Rect(
            rect.x + 56,
            chart_top,
            rect.width - 72,
            max(80, rect.bottom - chart_top - bottom_reserved),
        )

        if chart_rect.width <= 40 or chart_rect.height <= 40:
            return

        pygame.draw.rect(surface, (24, 24, 24), chart_rect, border_radius=10)

        # Inner plot area keeps lines/markers away from chart borders.
        marker_radius = 5
        plot_padding_x = 6
        plot_padding_y = 8
        plot_rect = pygame.Rect(
            chart_rect.x + plot_padding_x,
            chart_rect.y + plot_padding_y,
            max(1, chart_rect.width - (plot_padding_x * 2)),
            max(1, chart_rect.height - (plot_padding_y * 2)),
        )

        for index in range(5):
            y = chart_rect.y + int((chart_rect.height / 4) * index)
            pygame.draw.line(surface, (54, 54, 54), (chart_rect.x, y), (chart_rect.right, y), 1)

        for index in range(1, 6):
            x = chart_rect.x + int((chart_rect.width / 6) * index)
            pygame.draw.line(surface, (38, 38, 38), (x, chart_rect.y), (x, chart_rect.bottom), 1)

        pygame.draw.line(surface, theme.GRAY, (chart_rect.x, chart_rect.y), (chart_rect.x, chart_rect.bottom), 2)
        pygame.draw.line(surface, theme.GRAY, (chart_rect.x, chart_rect.bottom), (chart_rect.right, chart_rect.bottom), 2)

        # Keep axis labels aligned with the same safe plot band used by the lines.
        y_labels = [
            (plot_rect.top + marker_radius, "High"),
            (plot_rect.centery, "Mid"),
            (plot_rect.bottom - marker_radius, "Low"),
        ]
        for y, label in y_labels:
            label_text = theme.FONT_SMALL.render(label, True, theme.LIGHTER_GRAY)
            label_rect = label_text.get_rect(midright=(chart_rect.x - 10, y))
            surface.blit(label_text, label_rect)

        sample_count = len(self.metric_history)
        if sample_count >= 2:
            oldest_label = self._format_history_label(self.metric_history[0].get("timestamp"))
            newest_label = self._format_history_label(self.metric_history[-1].get("timestamp"))
            old_text = theme.FONT_SMALL.render(oldest_label, True, theme.LIGHT_GRAY)
            new_text = theme.FONT_SMALL.render(newest_label, True, theme.LIGHT_GRAY)
            surface.blit(old_text, (chart_rect.x, chart_rect.bottom + 8))
            new_rect = new_text.get_rect(topright=(chart_rect.right, chart_rect.bottom + 8))
            surface.blit(new_text, new_rect)

        old_clip = surface.get_clip()
        surface.set_clip(plot_rect)

        for metric_key in graph_metrics:
            points = []
            for index, entry in enumerate(self.metric_history):
                value = entry.get("metrics", {}).get(metric_key)
                if value is None:
                    continue

                normalized = self._normalize_metric_value(metric_key, value)
                x = plot_rect.x + int((plot_rect.width * index) / max(sample_count - 1, 1))

                y_span = max(1, plot_rect.height - (marker_radius * 2))
                y = plot_rect.bottom - marker_radius - int(normalized * y_span)

                # Clamp to keep all drawing within the safe plot area.
                x = max(plot_rect.left + marker_radius, min(x, plot_rect.right - marker_radius))
                y = max(plot_rect.top + marker_radius, min(y, plot_rect.bottom - marker_radius))
                points.append((x, y))

            if len(points) >= 2:
                pygame.draw.aalines(surface, self.GRAPH_COLORS[metric_key], False, points)
                pygame.draw.lines(surface, self.GRAPH_COLORS[metric_key], False, points, 3)
                pygame.draw.circle(surface, theme.WHITE, points[-1], 5)
                pygame.draw.circle(surface, self.GRAPH_COLORS[metric_key], points[-1], 3)

        surface.set_clip(old_clip)

        if not self.show_network_lines:
            self._draw_network_summary(surface, rect, selected_metrics)


    def _normalize_metric_value(self, metric_key, value):
        scale_limit = self.GRAPH_SCALE_LIMITS.get(metric_key, max(1.0, value))
        if scale_limit <= 0:
            return 0.0
        return max(0.0, min(value / scale_limit, 1.0))

    def _format_history_label(self, timestamp):
        if not timestamp:
            return ""
        if "T" not in str(timestamp):
            return str(timestamp)

        time_part = str(timestamp).split("T", 1)[1]
        return time_part.split(".", 1)[0]

    def _draw_averages_color_key(self, surface, rect, graph_metrics):
        """Draw color coding next to the averages table instead of inside the graph card."""
        pygame.draw.rect(surface, (34, 34, 34), rect, border_radius=8)
        header = theme.FONT_SMALL.render("Lines", True, theme.WHITE)
        surface.blit(header, (rect.x + 8, rect.y + 4))

        if not graph_metrics:
            return

        top = rect.y + 22
        row_h = max(14, min(20, (rect.height - 22) // max(1, len(graph_metrics))))
        for idx, metric_key in enumerate(graph_metrics):
            y = top + (idx * row_h)
            if y + row_h > rect.bottom:
                break

            color = self.GRAPH_COLORS[metric_key]
            pygame.draw.circle(surface, color, (rect.x + 12, y + 7), 4)
            label = self.GRAPH_SHORT_LABELS.get(metric_key, metric_key)
            text = theme.FONT_SMALL.render(label, True, theme.LIGHT_GRAY)
            surface.blit(text, (rect.x + 22, y))

    def _get_active_graph_metrics(self, averages):
        graph_metrics = [
            metric_key for metric_key in self.DEFAULT_GRAPH_METRICS
            if averages.get(metric_key) is not None
        ]

        if self.show_network_lines:
            graph_metrics.extend(
                metric_key for metric_key in self.NETWORK_GRAPH_METRICS
                if averages.get(metric_key) is not None
            )

        return graph_metrics

    def _draw_network_summary(self, surface, rect, averages):
        down = averages.get("net_rx_kbps")
        up = averages.get("net_tx_kbps")
        if down is None and up is None:
            return

        summary_rect = pygame.Rect(
            rect.x + theme.CARD_PADDING,
            rect.bottom - 28,
            rect.width - (theme.CARD_PADDING * 2),
            18,
        )

        parts = []
        if down is not None:
            parts.append(f"Down {utilities.format_metric_value('net_rx_kbps', down)}")
        if up is not None:
            parts.append(f"Up {utilities.format_metric_value('net_tx_kbps', up)}")

        label = "Net: " + "   ".join(parts)
        text = theme.FONT_SMALL.render(label, True, theme.LIGHTER_GRAY)
        surface.blit(text, (summary_rect.x, summary_rect.y))

    def _on_data_interpreted(self, payload):
        """Handle real-time data updates from the bus."""
        if isinstance(payload, dict) and "node" in payload:
            self.cache_data[payload["node"]] = payload
            self._refresh_graph_device_selector()
