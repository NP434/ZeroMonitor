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
                        print("Clicked device:", btn.device["name"])

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

        # Draw remaining contents on screen
        pygame.draw.rect(surface, theme.GRAY, (50, 150, 924, 120))
        text = theme.DEFAULT_FONT.render(
            "System stats here...",
            True,
            theme.WHITE
        )
        surface.blit(text, (60, 200))

        # Draw Button
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