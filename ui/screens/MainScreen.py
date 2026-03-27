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
        "disk_used_percent": "Disk Usage"
    }

    # Metric units for display
    METRIC_UNITS = {
        "cpu_load_1m": "",
        "cpu_temp_c": "°C",
        "mem_used_percent": "%",
        "mem_used_mb": "MB",
        "mem_total_mb": "MB",
        "disk_used_percent": "%"
    }

    def __init__(self, app):
        super().__init__(app)

        # Load assets
        self.load_assets()
        power_icon = pygame.transform.smoothscale(self.assets["power_button.png"], (40, 40))
        remove_icon = pygame.transform.smoothscale(self.assets["trash.png"], (40,40))
        
        # Create Power Button
        power_width = 60
        power_height = 60
        power_x = self.app.width - power_width - 10
        power_y = 20
        self.power_button = Button(
        rect=(power_x, power_y, power_width, power_height),
        image=power_icon,
        bg_color=theme.POWER_RED
        )

        # Create Settings Button
        settings_width = 160
        settings_height = 60
        settings_x = power_x - settings_width - 10
        settings_y = 20
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

        # Initalize device list
        self.device_buttons = []
        self.device_scroll = 0
        self._build_device_buttons()
        self.selected_device = None
        self.stat_buttons = {}

        # Other initializations/state variables
        self.popup = None
        self.cache_data = {}
        self._load_cache_data()

    def _load_cache_data(self):
        """Load cache data from cache_data.json"""
        cache_filepath = "data/cache_data.json"
        if os.path.exists(cache_filepath):
            try:
                with open(cache_filepath, 'r') as f:
                    self.cache_data = json.load(f)
            except Exception as e:
                print(f"Error loading cache_data.json: {e}")
                self.cache_data = {}


    def handle_event(self, event):
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            # Determine position based on event type
            if event.type == pygame.FINGERDOWN:
                # Finger coordinates are normalized (0.0 - 1.0)
                pos = (
                    int(event.x * self.app.width),
                    int(event.y * self.app.height)
                )
            else:
                # Mouse event provides pixel coordinates
                pos = event.pos

            # Handle popups
            if self.popup:
                self.popup.handle_event(event)
                if not self.popup.open:
                    self.popup = None
                return

            # Power Button clicked
            if self.power_button.is_clicked(pos):
                self.app.ui_control.stop_system()

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
                        self._build_stat_buttons()
                
                if self.remove_button.is_clicked(pos):
                    self._enter_remove_mode()

                # When user selects remove icon, open confirmation window
                if self.remove_mode:
                    for device_name, rbtn in self.remove_icons.items():
                        scrolled_rect = rbtn.rect.move(0, self.device_scroll)
                        if scrolled_rect.collidepoint(pos):
                            self.popup = ConfirmationPopup(
                                app=self.app,
                                message=f"Remove {device_name}?",
                                on_confirm=lambda name = device_name: self._confirm_remove(name),
                                on_cancel=self._exit_remove_mode
                            )
                            return

            # Selecting stat to show graph
            if self.selected_device:
                for key, btn in self.stat_buttons.items():
                    if btn.is_clicked(pos):
                        print(f"Clicked stat: {key}")

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_devices(event.y)

        self.sidebar.handle_event(event)

    def update(self):
        self.sidebar.update()
        # Reload cache data every frame to get latest metrics
        self._load_cache_data()

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Draw top bar background
        top_bar_height = 90
        pygame.draw.rect(surface, theme.DARK_GRAY, (0, 0, self.app.width, top_bar_height))
        pygame.draw.line(surface, theme.BLUE, (0, top_bar_height), (self.app.width, top_bar_height), 2)

        # --- Top Bar Elements ---

        # Time (topleft)
        if self.use_24hr:
            now = datetime.datetime.now().strftime("%H:%M")
        else:
            now = datetime.datetime.now().strftime("%I:%M %p")

        time_text = theme.FONT_MEDIUM.render(now, True, theme.BRIGHT_BLUE)
        surface.blit(time_text, (30, 25))

        # Title Centered Horizontally
        title_text = pygame.font.SysFont("Arial", 40, bold=True).render("⚡ Zero Monitor", True, theme.BRIGHT_BLUE)
        title_rect = title_text.get_rect(center=(self.app.width // 2, 45))
        surface.blit(title_text, title_rect)

        # Draw Settings Button
        self.settings_button.draw(surface)

        # Draw Power Button
        self.power_button.draw(surface)

        # Draw selected device name
        if self.selected_device:
            sidebar_width = self.sidebar.current_width
            content_area_width = self.app.width - sidebar_width
            content_start_x = sidebar_width + 50
            content_center_x = sidebar_width + content_area_width // 2

            # Device title
            title_font = pygame.font.SysFont("Arial", 36, bold=True)
            name_text = title_font.render(f"{self.selected_device['name']}", True, theme.BLUE)
            name_rect = name_text.get_rect(center=(content_center_x, 130))
            surface.blit(name_text, name_rect)

            # Horizontal line separator
            pygame.draw.line(surface, theme.GRAY, (content_start_x, 160), (self.app.width - 30, 160), 2)

            # Get device data from cache
            device_name = self.selected_device["name"]
            device_data = self.cache_data.get(device_name, {})
            metrics = device_data.get("metrics", {})
            severities = device_data.get("severities", {})
            timestamp = device_data.get("timestamp", "N/A")

            # Display timestamp in smaller font
            timestamp_parts = timestamp.split("T")
            timestamp_display = f"Updated: {timestamp_parts[0]} {timestamp_parts[1].split('.')[0]}" if "T" in timestamp else f"Updated: {timestamp}"
            timestamp_text = theme.FONT_SMALL.render(timestamp_display, True, theme.GRAY)
            surface.blit(timestamp_text, (content_start_x, 175))

            # Display metrics in single column for better clarity
            metric_y = 220
            metric_spacing = 75
            content_area_width = self.app.width - sidebar_width - 80

            metrics_list = list(metrics.items())

            for metric_name, metric_value in metrics_list:
                severity = severities.get(metric_name, "normal")
                severity_color = theme.STATUS_COLORS.get(severity, theme.WHITE)

                # Get friendly metric name and unit
                friendly_name = self.METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())
                unit = self.METRIC_UNITS.get(metric_name, "")

                # Format metric display
                if isinstance(metric_value, float):
                    display_value = f"{metric_value:.2f}"
                else:
                    display_value = str(metric_value)

                # Draw metric background box
                metric_box_width = content_area_width - 40
                metric_box_height = 60
                metric_box = pygame.Rect(content_start_x - 15, metric_y - 15, metric_box_width, metric_box_height)

                # Draw background
                pygame.draw.rect(surface, (20, 20, 20), metric_box, border_radius=12)
                # Draw colored border
                pygame.draw.rect(surface, severity_color, metric_box, 3, border_radius=12)

                # Draw metric label (left side)
                label_font = pygame.font.SysFont("Arial", 22)
                label_text = label_font.render(friendly_name, True, theme.WHITE)
                surface.blit(label_text, (content_start_x + 10, metric_y - 8))

                # Draw metric value with unit (right side)
                value_with_unit = f"{display_value}{unit}"
                value_font = pygame.font.SysFont("Arial", 34, bold=True)
                value_text = value_font.render(value_with_unit, True, severity_color)
                value_rect = value_text.get_rect(right=content_start_x + metric_box_width - 30, centery=metric_y + 8)
                surface.blit(value_text, value_rect)

                metric_y += metric_spacing

        # Draw stat buttons centered
        if self.selected_device:
            self._layout_stat_buttons()
            for btn in self.stat_buttons.values():
                btn.draw(surface)
        else:
            placeholder_font = pygame.font.SysFont("Arial", 32)
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

    def scroll_devices(self, direction):
        scroll_amount = 20
        self.device_scroll += direction * scroll_amount

        # Calculate spacing in between buttons
        if len(self.device_buttons) > 1 :
            first = self.device_buttons[0].rect
            second = self.device_buttons[1].rect
            spacing = second.y - first.y - first.height
        else:
            spacing = 0

        # Calculate total height of all device buttons
        total_height = 0
        for btn in self.device_buttons:
            total_height += btn.rect.height + spacing
        
        visible_height = self.sidebar.height - 60
        max_scroll = 0
        min_scroll = min(0, visible_height - total_height)

        # Clamp
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
        
        # Create the stat buttons based on keys in the stats dictionary
        for key, value in stats.items():
            self.stat_buttons[key] = Button(
                rect=pygame.Rect(0,0,200,200),
                text=f"{key}: {value}"
            )

    def _layout_stat_buttons(self):
        if not self.selected_device:
            return
        
        button_width = 200
        button_height = 60
        spacing = 40

        count = len(self.stat_buttons)
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
        # Remove from backend by calling ui_control method
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