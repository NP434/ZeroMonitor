import datetime
import pygame
import json
import os
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.SidebarPanel import SidebarPanel
from ui.widgets.ConfirmationPopup import ConfirmationPopup
import ui.theme as theme


class MainScreen(BaseScreen):
    """
    Dashboard/main screen that users will see
    """

    # Friendly metric display names
    METRIC_NAMES = {
        "cpu_load_1m": "CPU Load (1m)",
        "cpu_temp_c": "CPU Temperature",
        "mem_used_percent": "Memory Usage",
        "mem_used_mb": "Memory Used",
        "mem_total_mb": "Memory Total",
        "disk_used_percent": "Disk Usage",
        "core_voltage_v": "Core Voltage",
        "cpu_clock_mhz": "CPU Clock",
        "uptime_seconds": "Uptime",
        "net_rx_kbps": "Network Download",
        "net_tx_kbps": "Network Upload",
    }

    # Metric units for display
    METRIC_UNITS = {
        "cpu_load_1m": "",
        "cpu_temp_c": " C",
        "mem_used_percent": "%",
        "mem_used_mb": " MB",
        "mem_total_mb": " MB",
        "disk_used_percent": "%",
        "core_voltage_v": " V",
        "cpu_clock_mhz": " MHz",
        "uptime_seconds": "",
        "net_rx_kbps": " kbps",
        "net_tx_kbps": " kbps",
    }

    METRIC_ORDER = [
        "cpu_load_1m",
        "cpu_temp_c",
        "mem_used_percent",
        "disk_used_percent",
        "mem_used_mb",
        "mem_total_mb",
        "cpu_clock_mhz",
        "core_voltage_v",
        "net_rx_kbps",
        "net_tx_kbps",
        "uptime_seconds",
    ]

    def __init__(self, app):
        super().__init__(app)

        # Load assets
        self.load_assets()
        power_icon = pygame.transform.smoothscale(self.assets["power_button.png"], (40, 40))
        remove_icon = pygame.transform.smoothscale(self.assets["trash.png"], (40, 40))

        # Create Power Button with consistent spacing
        power_width = 50
        power_height = 50
        power_x = self.app.width - power_width - theme.MARGIN_XLARGE
        power_y = theme.MARGIN_LARGE + 5
        self.power_button = Button(
            rect=(power_x, power_y, power_width, power_height),
            image=power_icon,
            bg_color=theme.POWER_RED
        )

        # Create Dashboard Button with consistent sizing
        dashboard_width = 130
        dashboard_height = 45
        dashboard_x = power_x - dashboard_width - theme.GAP_LARGE
        dashboard_y = theme.MARGIN_LARGE + 8
        self.dashboard_button = Button(
            rect=(dashboard_x, dashboard_y, dashboard_width, dashboard_height),
            bg_color=theme.BLUE,
            text="Dashboard"
        )

        # Create Settings Button
        settings_width = 130
        settings_height = 45
        settings_x = dashboard_x - settings_width - theme.GAP_LARGE
        settings_y = theme.MARGIN_LARGE + 8
        self.settings_button = Button(
            rect=(settings_x, settings_y, settings_width, settings_height),
            bg_color=theme.BLUE,
            text="Settings"
        )

        # Create clock button
        self.clock_button = Button(
            rect=(20, 20, 150, 40),
            text="",
            bg_color=None,
            border_radius=0
        )
        self.use_24hr = False

        # Create sidebar panel
        self.sidebar = SidebarPanel(
            self.app,
            x=0,
            y=0,
            width_expanded=250,
            width_collapsed=40,
            height=app.height
        )

        # Create Remove Device Button
        remove_width = 50
        remove_height = 50
        remove_x = self.sidebar.x + (self.sidebar.width_expanded - remove_width) // 2
        remove_y = self.app.height - remove_height - 20
        self.remove_button = Button(
            rect=(remove_x, remove_y, remove_width, remove_height),
            text="-",
            image=remove_icon,
            bg_color=theme.POWER_RED
        )
        self.remove_mode = False
        self.remove_icons = {}
        
        #Create Add Devic Button
        add_width = 50
        add_height = 50
        add_x = self.sidebar.x + (self.sidebar.width_expanded - add_width) // 2
        add_y = self.app.height - add_height - 70
        self.add_button = Button(
            rect=(add_x,add_y,add_width,add_height),
            text="+",
            image = None,
            bg_color=theme.GREEN
        )
        self.add_mode = False

        # Initialize device list
        self.device_buttons = []
        self.device_scroll = 0
        self._build_device_buttons()
        self.selected_device = None
        self.stat_buttons = {}

        # Other initializations/state variables
        self.popup = None
        self.cache_data = {}
        self._load_cache_data()

        # Independent scroll state for metric card viewport
        self.metric_scroll = 0
        self.metric_content_height = 0
        self.metric_viewport_rect = None
        self.metric_scrollbar_track_rect = None
        self.metric_scrollbar_thumb_rect = None
        self.metric_drag_active = False
        self.metric_drag_pointer_id = None
        self.metric_drag_thumb_offset_y = 0

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


    def handle_event(self, event):
        pos = self._event_pos(event)

        if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            self.metric_drag_active = False
            self.metric_drag_pointer_id = None

        elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION) and self.metric_drag_active:
            if event.type == pygame.FINGERMOTION and self.metric_drag_pointer_id is not None:
                if event.finger_id != self.metric_drag_pointer_id:
                    self.sidebar.handle_event(event)
                    return

            if pos is not None:
                self._set_metric_scroll_from_thumb_top(pos[1] - self.metric_drag_thumb_offset_y)

        elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if self._try_start_metric_scroll_drag(event, pos):
                return

            # Handle popups
            if self.popup:
                self.popup.handle_event(event)
                if not self.popup.open:
                    self.popup = None
                return

            # Power Button clicked
            if self.power_button.is_clicked(pos):
                self.app.ui_control.stop_system()

            # Dashboard button clicked
            if self.dashboard_button.is_clicked(pos):
                self.app.change_screen("dashboard")

            # Settings button clicked
            if self.settings_button.is_clicked(pos):
                self.app.change_screen("settings")
                return

            # Clock button clicked
            if self.clock_button.is_clicked(pos):
                self.use_24hr = not self.use_24hr

            # Sidebar expanded
            if self.sidebar.current_width > self.sidebar.width_collapsed + 20:
                for btn in self.device_buttons:
                    scrolled_rect = btn.rect.move(0, self.device_scroll)
                    if scrolled_rect.collidepoint(pos):
                        self.selected_device = btn.device
                        self.metric_scroll = 0
                        self._build_stat_buttons()

                if self.remove_button.is_clicked(pos):
                    self._enter_remove_mode()

                if self.add_button.is_clicked(pos):
                    self.app.change_screen("add_device")
                    

                # When user selects remove icon, open confirmation window
                if self.remove_mode:
                    for device_name, rbtn in self.remove_icons.items():
                        scrolled_rect = rbtn.rect.move(0, self.device_scroll)
                        if scrolled_rect.collidepoint(pos):
                            self.popup = ConfirmationPopup(
                                app=self.app,
                                message=f"Remove {device_name}?",
                                on_confirm=lambda name=device_name: self._confirm_remove(name),
                                on_cancel=self._exit_remove_mode
                            )
                            return

            # Selecting stat to show graph
            if self.selected_device:
                for key, btn in self.stat_buttons.items():
                    if btn.is_clicked(pos):
                        print(f"Clicked stat: {key}")

        elif event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] <= self.sidebar.current_width:
                self.scroll_devices(event.y)
            elif self.selected_device and self.metric_viewport_rect and self.metric_viewport_rect.collidepoint(mouse_pos):
                self.scroll_metrics(event.y)
            else:
                self.scroll_devices(event.y)

        self.sidebar.handle_event(event)

    def _event_pos(self, event):
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return (int(event.x * self.app.width), int(event.y * self.app.height))
        if hasattr(event, "pos"):
            return event.pos
        return None

    def _try_start_metric_scroll_drag(self, event, pos):
        if not self.selected_device or pos is None:
            return False
        if not self.metric_scrollbar_thumb_rect:
            return False

        if self.metric_scrollbar_thumb_rect.collidepoint(pos):
            self.metric_drag_active = True
            self.metric_drag_thumb_offset_y = pos[1] - self.metric_scrollbar_thumb_rect.y
            self.metric_drag_pointer_id = getattr(event, "finger_id", None)
            return True

        return False

    def update(self):
        self.sidebar.update()
        # Reload cache data every frame to get latest metrics
        self._load_cache_data()

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Draw top bar background with improved styling
        pygame.draw.rect(surface, theme.TOPBAR_BG, (0, 0, self.app.width, theme.TOPBAR_HEIGHT))
        pygame.draw.line(surface, theme.TOPBAR_BORDER_COLOR, (0, theme.TOPBAR_HEIGHT),
                        (self.app.width, theme.TOPBAR_HEIGHT), theme.TOPBAR_BORDER_WIDTH)

        if self.use_24hr:
            now = datetime.datetime.now().strftime("%H:%M")
        else:
            now = datetime.datetime.now().strftime("%I:%M %p")

        time_text = theme.FONT_MEDIUM.render(now, True, theme.BRIGHT_BLUE)
        surface.blit(time_text, (theme.MARGIN_XLARGE, theme.MARGIN_LARGE + 5))

        # Use theme title font
        title_text = theme.FONT_TITLE.render("Devices", True, theme.BRIGHT_BLUE)
        title_rect = title_text.get_rect(center=(self.app.width // 2, theme.TOPBAR_HEIGHT // 2 + 5))
        surface.blit(title_text, title_rect)

        self.dashboard_button.draw(surface)
        self.settings_button.draw(surface)
        self.power_button.draw(surface)

        if self.selected_device:
            sidebar_width = self.sidebar.current_width
            content_left = sidebar_width + theme.MARGIN_XLARGE
            content_right = self.app.width - theme.MARGIN_LARGE
            content_width = max(260, content_right - content_left)
            content_center_x = content_left + content_width // 2

            # Device name with improved typography
            device_name_font = theme.FONT_XLARGE
            device_name = device_name_font.render(f"{self.selected_device['name']}", True, theme.BRIGHT_BLUE)
            device_name_rect = device_name.get_rect(center=(content_center_x, theme.TOPBAR_HEIGHT + 35))
            surface.blit(device_name, device_name_rect)

            # Better separator line
            pygame.draw.line(surface, theme.GRAY, (content_left, theme.TOPBAR_HEIGHT + 65),
                           (content_right, theme.TOPBAR_HEIGHT + 65), theme.BORDER_WIDTH_MEDIUM)

            device_name_key = self.selected_device["name"]
            device_data = self.cache_data.get(device_name_key, {})
            metrics = device_data.get("metrics", {})
            severities = device_data.get("severities", {})
            timestamp = self._format_timestamp(device_data.get("timestamp", "N/A"))

            # Timestamp with better styling
            timestamp_text = theme.FONT_SMALL.render(f"Last updated: {timestamp}", True, theme.LIGHT_GRAY)
            surface.blit(timestamp_text, (content_left, theme.TOPBAR_HEIGHT + 75))

            # Build a stable metric list with preferred order first, then any extras.
            ordered_metrics = []
            seen = set()
            for key in self.METRIC_ORDER:
                if key in metrics:
                    ordered_metrics.append((key, metrics.get(key)))
                    seen.add(key)
            for key, value in metrics.items():
                if key not in seen:
                    ordered_metrics.append((key, value))

            # Improved metric card grid with better spacing
            grid_top = theme.TOPBAR_HEIGHT + 110
            card_gap = theme.GAP_LARGE
            card_height = 90
            columns = 2
            card_width = (content_width - card_gap) // columns

            rows = (len(ordered_metrics) + columns - 1) // columns
            self.metric_content_height = max(0, rows * (card_height + card_gap) - card_gap)

            viewport_bottom = self.app.height - theme.MARGIN_LARGE
            self.metric_viewport_rect = pygame.Rect(
                content_left,
                grid_top,
                content_width,
                max(0, viewport_bottom - grid_top),
            )
            self._clamp_metric_scroll()

            old_clip = surface.get_clip()
            surface.set_clip(self.metric_viewport_rect)

            for idx, (metric_name, metric_value) in enumerate(ordered_metrics):
                row = idx // columns
                col = idx % columns
                x = content_left + (col * (card_width + card_gap))
                y = grid_top + row * (card_height + card_gap) + self.metric_scroll
                rect = pygame.Rect(x, y, card_width, card_height)

                if not rect.colliderect(self.metric_viewport_rect):
                    continue

                friendly_name = self.METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())
                severity = severities.get(metric_name, "normal")
                value_text = self._format_metric_value(metric_name, metric_value)
                self._draw_metric_card(surface, rect, friendly_name, value_text, severity)

            surface.set_clip(old_clip)
            self._draw_metric_scrollbar(surface)
        else:
            placeholder_font = pygame.font.SysFont("Arial", 30)
            placeholder = placeholder_font.render("Select a device to view stats", True, theme.LIGHT_GRAY)
            placeholder_rect = placeholder.get_rect(center=(self.app.width // 2, self.app.height // 2))
            surface.blit(placeholder, placeholder_rect)

        # --- Side Bar Elements ---

        # Draw sidebar
        self.sidebar.draw(surface)

        # Draw device buttons when sidebar is expanded
        if self.sidebar.current_width > self.sidebar.width_collapsed + 20:
            for btn in self.device_buttons:
                scrolled_rect = btn.rect.move(0, self.device_scroll)
                if scrolled_rect.bottom < 0 or scrolled_rect.top > self.app.height:
                    continue

                original_rect = btn.rect
                btn.rect = scrolled_rect
                btn.draw(surface)
                btn.rect = original_rect

            self.remove_button.draw(surface)
            self.add_button.draw(surface)

            # Draw remove buttons
            if self.remove_mode:
                for name, rbtn in self.remove_icons.items():
                    scrolled_rect = rbtn.rect.move(0, self.device_scroll)
                    original_rect = rbtn.rect
                    rbtn.rect = scrolled_rect
                    rbtn.draw(surface)
                    rbtn.rect = original_rect

        # Draw popup
        if self.popup:
            self.popup.draw(surface)

    def _format_timestamp(self, timestamp):
        if isinstance(timestamp, str) and "T" in timestamp:
            date_part, time_part = timestamp.split("T", 1)
            return f"{date_part} {time_part.split('.')[0]}"
        return str(timestamp)

    def _format_metric_value(self, metric_name, metric_value):
        if metric_value is None:
            return "N/A"

        if metric_name == "uptime_seconds":
            total = int(metric_value)
            days = total // 86400
            hours = (total % 86400) // 3600
            mins = (total % 3600) // 60
            if days > 0:
                return f"{days}d {hours}h {mins}m"
            return f"{hours}h {mins}m"

        if metric_name in {"net_rx_kbps", "net_tx_kbps"}:
            if metric_value >= 1000:
                return f"{metric_value / 1000.0:.2f} Mbps"
            return f"{metric_value:.0f} kbps"

        if metric_name in {"mem_used_mb", "mem_total_mb"}:
            return f"{int(metric_value)}{self.METRIC_UNITS.get(metric_name, '')}"

        if metric_name == "cpu_load_1m":
            return f"{metric_value:.2f}"

        if isinstance(metric_value, float):
            return f"{metric_value:.2f}{self.METRIC_UNITS.get(metric_name, '')}"

        return f"{metric_value}{self.METRIC_UNITS.get(metric_name, '')}"

    def _draw_metric_card(self, surface, rect, label, value, severity):
        severity_color = theme.STATUS_COLORS.get(severity, theme.WHITE)

        # Draw card background with rounded corners
        pygame.draw.rect(surface, theme.CARD_BG, rect, border_radius=theme.CARD_CORNER_RADIUS)
        # Draw border based on severity
        pygame.draw.rect(surface, severity_color, rect, theme.CARD_BORDER_WIDTH, border_radius=theme.CARD_CORNER_RADIUS)

        # Improved typography
        label_font = pygame.font.SysFont("Arial", 16)
        value_font = pygame.font.SysFont("Arial", 32, bold=True)

        label_text = label_font.render(label, True, theme.LIGHTER_GRAY)
        value_text = value_font.render(value, True, severity_color)

        # Better padding and alignment
        surface.blit(label_text, (rect.x + theme.CARD_PADDING, rect.y + theme.PADDING_MEDIUM))
        value_rect = value_text.get_rect(left=rect.x + theme.CARD_PADDING, bottom=rect.bottom - theme.PADDING_MEDIUM)
        surface.blit(value_text, value_rect)

    def _clamp_metric_scroll(self):
        if not self.metric_viewport_rect:
            self.metric_scroll = 0
            return

        visible = self.metric_viewport_rect.height
        min_scroll = min(0, visible - self.metric_content_height)

        if self.metric_scroll > 0:
            self.metric_scroll = 0
        elif self.metric_scroll < min_scroll:
            self.metric_scroll = min_scroll

    def scroll_metrics(self, direction):
        scroll_amount = 36
        self.metric_scroll += direction * scroll_amount
        self._clamp_metric_scroll()

    def _draw_metric_scrollbar(self, surface):
        if not self.metric_viewport_rect:
            self.metric_scrollbar_track_rect = None
            self.metric_scrollbar_thumb_rect = None
            return

        geometry = self._get_metric_scrollbar_geometry()
        if geometry is None:
            self.metric_scrollbar_track_rect = None
            self.metric_scrollbar_thumb_rect = None
            return

        track_rect, thumb_rect = geometry
        self.metric_scrollbar_track_rect = track_rect
        self.metric_scrollbar_thumb_rect = thumb_rect

        pygame.draw.rect(surface, (40, 40, 40), track_rect, border_radius=4)
        pygame.draw.rect(surface, theme.BRIGHT_BLUE, thumb_rect, border_radius=4)

    def _get_metric_scrollbar_geometry(self):
        if not self.metric_viewport_rect:
            return None
        if self.metric_content_height <= self.metric_viewport_rect.height:
            return None

        track_w = 8
        track_h = self.metric_viewport_rect.height
        track_x = self.metric_viewport_rect.right - track_w - 4
        track_y = self.metric_viewport_rect.y
        track_rect = pygame.Rect(track_x, track_y, track_w, track_h)

        visible_ratio = self.metric_viewport_rect.height / self.metric_content_height
        thumb_h = max(28, int(track_h * visible_ratio))
        max_offset = self.metric_content_height - self.metric_viewport_rect.height
        current_offset = -self.metric_scroll
        thumb_travel = max(1, track_h - thumb_h)
        thumb_y = track_y + int((current_offset / max_offset) * thumb_travel)
        thumb_rect = pygame.Rect(track_x, thumb_y, track_w, thumb_h)
        return track_rect, thumb_rect

    def _set_metric_scroll_from_thumb_top(self, thumb_top_y):
        geometry = self._get_metric_scrollbar_geometry()
        if geometry is None:
            return

        track_rect, thumb_rect = geometry
        min_thumb_y = track_rect.y
        max_thumb_y = track_rect.bottom - thumb_rect.height
        clamped_thumb_y = max(min_thumb_y, min(thumb_top_y, max_thumb_y))

        max_offset = self.metric_content_height - self.metric_viewport_rect.height
        thumb_travel = max(1, track_rect.height - thumb_rect.height)
        ratio = (clamped_thumb_y - min_thumb_y) / thumb_travel
        self.metric_scroll = -int(ratio * max_offset)
        self._clamp_metric_scroll()

    def scroll_devices(self, direction):
        scroll_amount = 20
        self.device_scroll += direction * scroll_amount

        if len(self.device_buttons) > 1:
            first = self.device_buttons[0].rect
            second = self.device_buttons[1].rect
            spacing = second.y - first.y - first.height
        else:
            spacing = 0

        total_height = 0
        for btn in self.device_buttons:
            total_height += btn.rect.height + spacing

        visible_height = self.sidebar.height - 60
        max_scroll = 0
        min_scroll = min(0, visible_height - total_height)

        if self.device_scroll > max_scroll:
            self.device_scroll = max_scroll
        elif self.device_scroll < min_scroll:
            self.device_scroll = min_scroll

    def _build_device_buttons(self):
        self.device_buttons = []

        button_width = self.sidebar.width_expanded - 20
        button_height = 60
        x = self.sidebar.x + 10
        y = 60

        remove_icon_space = 50 if self.remove_mode else 0

        for device in self.app.devices:
            status = device.get("status", "Offline")
            color = theme.STATUS_COLORS.get(status, (100, 100, 100))

            btn = Button(
                rect=(x + remove_icon_space, y, button_width - remove_icon_space, button_height),
                text=device["name"],
                bg_color=color
            )
            btn.device = device
            self.device_buttons.append(btn)

            y += button_height + 10

    def _build_stat_buttons(self):
        if not self.selected_device:
            return

        stats = self.selected_device.get("stats", {})
        self.stat_buttons = {}
        for key, value in stats.items():
            self.stat_buttons[key] = Button(
                rect=pygame.Rect(0, 0, 200, 200),
                text=f"{key}: {value}"
            )

    def _layout_stat_buttons(self):
        if not self.selected_device:
            return

        button_width = 200
        button_height = 60
        spacing = 40

        count = len(self.stat_buttons)
        if count == 0:
            return

        total_width = count * button_width + (count - 1) * spacing
        sidebar_width = self.sidebar.current_width

        x = sidebar_width + (self.app.width - sidebar_width - total_width) // 2
        y = self.app.height // 2

        for btn in self.stat_buttons.values():
            btn.rect.x = x
            btn.rect.y = y
            btn.rect.width = button_width
            btn.rect.height = button_height
            x += button_width + spacing

    def _enter_remove_mode(self):
        self.remove_mode = True
        self.remove_icons.clear()
        self._build_device_buttons()
        self._build_remove_icons()

    def _exit_remove_mode(self):
        self.remove_mode = False
        self.remove_icons.clear()
        self._build_device_buttons()

    def _confirm_remove(self, device_name):
        self.app.ui_control.remove_node(device_name)

    def _build_remove_icons(self):
        icon_size = 40
        padding = 10

        for btn in self.device_buttons:
            x = self.sidebar.x + padding
            scrolled_y = btn.rect.y + self.device_scroll
            y = scrolled_y + (btn.rect.height - icon_size) // 2

            remove_btn = Button(
                rect=(x, y, icon_size, icon_size),
                text="X",
                bg_color=theme.POWER_RED
            )

            self.remove_icons[btn.device["name"]] = remove_btn

