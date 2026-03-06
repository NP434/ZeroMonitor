import datetime
import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.SidebarPanel import SidebarPanel
from ui.widgets.ConfirmationPopup import ConfirmationPopup
import ui.theme as theme

class MainScreen(BaseScreen):
    """
    Dashboard/main screen that users will see
    """
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

        # Initalize device list
        self.device_buttons = []
        self.device_scroll = 0
        self._build_device_buttons()
        self.selected_device = None
        self.stat_buttons = {}

        # Other initializations/state variables
        self.popup = None


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

        # Draw Settings Button
        self.settings_button.draw(surface)

        # Draw Power Button
        self.power_button.draw(surface)

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
        self._build_device_buttons()
        self._build_remove_icons()

    def _exit_remove_mode(self):
        self.remove_mode = False
        self.remove_icons.clear()
        self._build_device_buttons()

    def _confirm_remove(self, device_name):
        # Remove from backend by calling ui_control method
        self.app.ui_control.remove_node(device_name)
        self._exit_remove_mode()

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