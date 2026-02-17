import datetime
import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.SidebarPanel import SidebarPanel
import ui.theme as theme

class MainScreen(BaseScreen):
    """
    Dashboard/main screen that users will see
    """
    def __init__(self, app):
        super().__init__(app)
    
        # Create settings button
        self.settings_button = Button(
            rect=(app.width - 180, 20, 160, 60),
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
            x=0,
            y=0,
            width_expanded=250,
            width_collapsed=40,
            height=app.height
        )

        # Initalize device list
        self.device_buttons = []
        self.device_scroll = 0
        self._build_device_buttons()
        self.selected_device = None
        self.stat_buttons = {}

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.settings_button.is_clicked(event.pos):
                self.app.change_screen("settings")
            
            if self.clock_button.is_clicked(event.pos):
                self.use_24hr = not self.use_24hr

            if self.sidebar.current_width > self.sidebar.width_collapsed + 20:
                for btn in self.device_buttons:
                    scrolled_rect = btn.rect.move(0, self.device_scroll)
                    if scrolled_rect.collidepoint(event.pos):
                        self.selected_device = btn.device
                        self._build_stat_buttons()

            if self.selected_device:
                for key, btn in self.stat_buttons.items():
                    if btn.is_clicked(event.pos):
                        print(f"Clicked stat: {key}")

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_devices(event.y)

        self.sidebar.handle_event(event)

    def update(self):
        self.sidebar.update()

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # --- Top Bar Elements ---

        # Time (topleft)
        if self.use_24hr:
            now = datetime.datetime.now().strftime("%H:%M")
        else:
            now = datetime.datetime.now().strftime("%I:%M %p")

        time_text = theme.DEFAULT_FONT.render(now, True, theme.WHITE)
        surface.blit(time_text, (20, 20))

        # Title Centered Horizontally
        title_text = theme.DEFAULT_FONT.render("Zero Monitor Dashboard", True, theme.WHITE)
        title_rect = title_text.get_rect(
            center=(self.app.width // 2, 50)
        )
        surface.blit(title_text, title_rect)

        # Draw selected device name
        if self.selected_device:
            name_text = theme.DEFAULT_FONT.render(f"{self.selected_device["name"]} Stats", True, theme.WHITE)
            name_rect = name_text.get_rect(center=(self.app.width // 2, 100))
            surface.blit(name_text, name_rect)

        # Draw stat buttons centered
        if self.selected_device:
            self._layout_stat_buttons()
            for btn in self.stat_buttons.values():
                btn.draw(surface)
        else:
            placeholder = theme.DEFAULT_FONT.render("Select a device to view stats", True, theme.WHITE)
            surface.blit(placeholder, (self.app.width // 2 - placeholder.get_width() // 200, 200))
        
        # Draw Settings Button
        self.settings_button.draw(surface)

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
        button_width = self.sidebar.width_expanded - 20
        button_height = 40
        x = self.sidebar.x + 10
        y = 60

        for device in self.app.devices:
            status = device.get("status", "Offline")
            color = theme.STATUS_COLORS.get(status, (100, 100, 100))

            btn = Button(
                rect=(x, y, button_width, button_height),
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