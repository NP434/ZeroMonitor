"""
Filename: SettingsScreen.py

Unified settings screen with System | Device pill tabs inline in the header.
"""

import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.Slider import Slider
from ui.widgets.Dropdown import DropDown
from ui.widgets.ConfirmationPopup import ConfirmationPopup
from ui.widgets.ToggleSwitch import ToggleSwitch
import ui.theme as theme
import ui.utilities as utilities


TAB_SYSTEM = "system"
TAB_DEVICE = "device"

# Height of the single header bar that holds title + tabs + back button
HEADER_H = 70
# Where the content area begins (just below the header + a divider line)
CONTENT_Y = HEADER_H + 2


class SettingsScreen(BaseScreen):
    """
    Single settings screen
    """

    POLLING_MAP = {"Low": 30, "Medium": 15, "High": 5}

    def __init__(self, app):
        super().__init__(app)
        self.load_assets()

        # ── state ──────────────────────────────────────────────────────────
        self.active_tab = TAB_SYSTEM
        self.confirm_popup = None
        self._pending_action = None

        # Device-tab state
        self.selected_device = None
        self.device_buttons = {}
        self.device_settings_widgets = []
        self.unsaved_changes = False
        self.sidebar_width = 220
        self.scroll_offset = 0

        # System-tab state
        self.system_unsaved = False

        # ── Back / home button (far left of header) ────────────────────────
        house_icon = pygame.transform.smoothscale(self.assets["house.png"], (26, 26))
        self.back_btn = Button(
            pygame.Rect(10, (HEADER_H - 46) // 2, 46, 46),
            image=house_icon,
            bg_color=theme.BLUE,
            border_radius=14,
        )

        # ── Pill tab buttons (right side of header) ────────────────────────
        tab_w = 120
        tab_h = 38
        tab_y = (HEADER_H - tab_h) // 2
        gap = 8
        right_margin = 14

        self.tab_device_btn = Button(
            pygame.Rect(app.width - right_margin - tab_w, tab_y, tab_w, tab_h),
            text="Device",
            bg_color=theme.DARK_GRAY,
            border_radius=19,          # fully rounded pill
        )
        self.tab_system_btn = Button(
            pygame.Rect(app.width - right_margin - tab_w * 2 - gap, tab_y, tab_w, tab_h),
            text="System",
            bg_color=theme.BLUE,
            border_radius=19,
        )

        # ── System tab widgets ─────────────────────────────────────────────
        #
        # Layout:
        #   CONTENT_Y + 20  →  section heading
        #   CONTENT_Y + 60  →  "Brightness  50%" label
        #   CONTENT_Y + 90  →  slider track
        #   CONTENT_Y + 150 →  Apply button
        #
        slider_x = app.width // 2 - 280
        slider_y = CONTENT_Y + 90
        slider_w = 560

        self.brightness_slider = Slider(
            app,
            rect=(slider_x, slider_y, slider_w, 20),
            min_value=0,
            max_value=100,
            default_value=50,
            label="Brightness",
            track_color=theme.BLUE,
            on_change=self._on_brightness_change,
        )
        self.brightness_value = 50
        self._saved_brightness = 50       # track what has been applied

        apply_w = 180
        self.system_apply_btn = Button(
            pygame.Rect(app.width // 2 - apply_w // 2, slider_y + 50, apply_w, 42),
            text="Apply",
            bg_color=theme.DARK_GRAY,   # starts greyed — nothing unsaved yet
            border_radius=10,
        )

        # ── Device tab widgets ─────────────────────────────────────────────
        self._build_device_list()

        self.device_apply_btn = Button(
            pygame.Rect(10, app.height - 54, self.sidebar_width - 20, 42),
            text="Apply Changes",
            bg_color=theme.GREEN,
            border_radius=10,
        )

    # ══════════════════════════════════════════════════════════════════════
    # System tab
    # ══════════════════════════════════════════════════════════════════════

    def _on_brightness_change(self, value):
        self.brightness_value = value
        self.system_unsaved = (round(value) != round(self._saved_brightness))
        self.app.ui_control.preview_brightness(value)

    def _apply_system(self):
        self._saved_brightness = self.brightness_value
        self.system_unsaved = False
        self.app.ui_control.set_brightness(self.brightness_value)

    # ══════════════════════════════════════════════════════════════════════
    # Device tab
    # ══════════════════════════════════════════════════════════════════════

    def _build_device_list(self):
        self.device_buttons.clear()
        x = 10
        y = CONTENT_Y + 10
        w = self.sidebar_width - 20
        h = 56

        for device in self.app.devices:
            name = device["name"]
            self.device_buttons[name] = Button(
                pygame.Rect(x, y, w, h),
                text=name,
                bg_color=None,
                text_color=theme.WHITE,
                border_radius=10,
                align="left",
            )
            y += h + 8

    def _get_device(self, name):
        for d in self.app.devices:
            if d["name"] == name:
                return d
        return None

    def _build_settings_widgets(self):
        """Rebuild right-panel widgets for the currently selected device."""
        self.device_settings_widgets = []
        if not self.selected_device:
            return

        device = self._get_device(self.selected_device)
        panel_x = self.sidebar_width + 40

        # Each setting row occupies a label + widget block.
        # Label sits SETTING_ROW_H px below CONTENT_Y,
        # widget sits LABEL_H px below that — no overlap possible.
        FIRST_ROW_Y = CONTENT_Y + 80   # first setting row (below device heading)
        LABEL_H     = 26               # height reserved for the label text
        ROW_STRIDE  = 80               # vertical distance between row starts

        row_y = FIRST_ROW_Y

        # ── Polling frequency row ──────────────────────────────────────────
        poll_seconds  = int(device.get("polling_frequency", 15))
        default_label = self._polling_label(poll_seconds)

        poll_dropdown = DropDown(
            self.app,
            pygame.Rect(panel_x, row_y + LABEL_H, 200, 40),
            ["Low", "Medium", "High"],
            default=default_label,
        )
        poll_dropdown._label_y = row_y   # draw() uses this for the label

        self.device_settings_widgets.append(("poll_rate", poll_dropdown))
        row_y += ROW_STRIDE

        # ── Pause Polling row ─────────────────────────────────────────────
        pause_toggle = ToggleSwitch(
            self.app,
            rect=(panel_x, row_y + LABEL_H, 60, 32),
            default=device.get("polling_paused", False)
        )
        pause_toggle._label_y = row_y

        self.device_settings_widgets.append(("polling_paused", pause_toggle))
        row_y += ROW_STRIDE

        # ── Add more rows here later (same pattern) ────────────────────────
        # example:
        #   some_widget = SomeWidget(..., rect=(panel_x, row_y + LABEL_H, ...))
        #   some_widget._label_y = row_y
        #   self.device_settings_widgets.append(("some_key", some_widget))
        #   row_y += ROW_STRIDE

    def _polling_label(self, seconds):
        if seconds >= 25:
            return "Low"
        elif seconds >= 10:
            return "Medium"
        return "High"

    def _apply_device(self):
        if not self.unsaved_changes or not self.selected_device:
            return
        device = self._get_device(self.selected_device)
        for key, widget in self.device_settings_widgets:
            if key == "poll_rate":
                numeric = self.POLLING_MAP.get(widget.selected, 15)
                self.app.ui_control.change_polling_rate(device["name"], numeric)

            if key == "polling_paused":
                self.app.ui_control.pause_polling(device["name"], widget.value)
        self.unsaved_changes = False

    # ══════════════════════════════════════════════════════════════════════
    # Tab switching
    # ══════════════════════════════════════════════════════════════════════

    def _switch_tab(self, tab):
        if tab == self.active_tab:
            return
        unsaved = self.system_unsaved if self.active_tab == TAB_SYSTEM else self.unsaved_changes
        if unsaved:
            self._pending_action = lambda: self._do_switch_tab(tab)
            msg = ("Apply brightness before switching?"
                   if self.active_tab == TAB_SYSTEM
                   else "Apply changes before switching?")
            self._open_confirm(msg)
        else:
            self._do_switch_tab(tab)

    def _do_switch_tab(self, tab):
        self.active_tab = tab
        self.tab_system_btn.bg_color = theme.BLUE if tab == TAB_SYSTEM else theme.DARK_GRAY
        self.tab_device_btn.bg_color = theme.BLUE if tab == TAB_DEVICE else theme.DARK_GRAY

    # ══════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════

    def _go_home(self):
        unsaved = self.system_unsaved if self.active_tab == TAB_SYSTEM else self.unsaved_changes
        if unsaved:
            self._pending_action = lambda: self.app.change_screen("main")
            msg = ("Apply brightness before leaving?"
                   if self.active_tab == TAB_SYSTEM
                   else "Apply changes before leaving?")
            self._open_confirm(msg)
        else:
            self.app.change_screen("main")

    # ══════════════════════════════════════════════════════════════════════
    # Confirmation popup
    # ══════════════════════════════════════════════════════════════════════

    def _open_confirm(self, message):
        self.confirm_popup = ConfirmationPopup(
            self.app,
            message,
            on_confirm=self._confirm_apply_and_run,
            on_cancel=self._discard_and_run,
        )

    def _confirm_apply_and_run(self):
        if self.active_tab == TAB_SYSTEM:
            self._apply_system()
        else:
            self._apply_device()
        self._run_pending()

    def _discard_and_run(self):
        if self.active_tab == TAB_SYSTEM:
            self.brightness_value = self._saved_brightness
            self.brightness_slider.value = self._saved_brightness
            self.system_unsaved = False
        else:
            self.unsaved_changes = False
            self._build_settings_widgets()
        self._run_pending()

    def _run_pending(self):
        self.confirm_popup = None
        if self._pending_action:
            self._pending_action()
        self._pending_action = None

    # ══════════════════════════════════════════════════════════════════════
    # Event handling
    # ══════════════════════════════════════════════════════════════════════

    def handle_event(self, event):
        if self.confirm_popup:
            self.confirm_popup.handle_event(event)
            return

        # Slider needs all event types (drag / motion), not just clicks
        if self.active_tab == TAB_SYSTEM:
            self.brightness_slider.handle_event(event)

        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return

        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            return

        # ── Header ────────────────────────────────────────────────────────
        if self.back_btn.is_clicked(pos):
            self._go_home()
            return

        if self.tab_system_btn.is_clicked(pos):
            self._switch_tab(TAB_SYSTEM)
            return

        if self.tab_device_btn.is_clicked(pos):
            self._switch_tab(TAB_DEVICE)
            return

        # ── System tab ────────────────────────────────────────────────────
        if self.active_tab == TAB_SYSTEM:
            if self.system_unsaved and self.system_apply_btn.is_clicked(pos):
                self._apply_system()
            return

        # ── Device tab ────────────────────────────────────────────────────
        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)
            if r.collidepoint(pos):
                self.selected_device = name
                self._build_settings_widgets()
                return

        if self.selected_device:
            for key, widget in self.device_settings_widgets:
                result = widget.handle_event(event)
                if result is not None:
                    device = self._get_device(self.selected_device)
                    device[key] = result
                    self.unsaved_changes = True

        if self.device_apply_btn.is_clicked(pos):
            self._apply_device()

    # ══════════════════════════════════════════════════════════════════════
    # Drawing
    # ══════════════════════════════════════════════════════════════════════

    def draw(self, surface):
        surface.fill(theme.BLACK)
        self._draw_header(surface)

        if self.active_tab == TAB_SYSTEM:
            self._draw_system_tab(surface)
        else:
            self._draw_device_tab(surface)

        if self.confirm_popup:
            self.confirm_popup.draw(surface)

    def _draw_header(self, surface):
        pygame.draw.rect(surface, theme.DARK_GRAY,
                         (0, 0, self.app.width, HEADER_H))
        pygame.draw.line(surface, theme.BLUE,
                         (0, HEADER_H), (self.app.width, HEADER_H), 2)

        title = theme.FONT_MEDIUM.render("Settings", True, theme.BRIGHT_BLUE)
        surface.blit(title, (self.app.width // 2 - title.get_width() // 2,
                              HEADER_H // 2 - title.get_height() // 2))

        self.back_btn.draw(surface)
        self.tab_system_btn.draw(surface)
        self.tab_device_btn.draw(surface)

    def _draw_system_tab(self, surface):
        heading = theme.FONT_MEDIUM.render("System Settings", True, theme.WHITE)
        surface.blit(heading, (self.app.width // 2 - heading.get_width() // 2,
                                CONTENT_Y + 20))

        # Unsaved indicator (same style as device tab)
        if self.system_unsaved:
            dot = theme.FONT_SMALL.render("● unsaved changes", True, theme.YELLOW)
            surface.blit(dot, (self.app.width // 2 - dot.get_width() // 2,
                            CONTENT_Y + 46))



        self.brightness_slider.draw(surface)

        # Apply button: green when there's something to save, dark grey otherwise
        self.system_apply_btn.bg_color = (theme.GREEN if self.system_unsaved
                                          else theme.DARK_GRAY)
        self.system_apply_btn.draw(surface)

    def _draw_device_tab(self, surface):
        # Sidebar
        pygame.draw.rect(surface, theme.GRAY,
                         (0, CONTENT_Y, self.sidebar_width, self.app.height))
        pygame.draw.line(surface, theme.WHITE,
                         (self.sidebar_width, CONTENT_Y),
                         (self.sidebar_width, self.app.height), 1)

        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)
            if name == self.selected_device:
                pygame.draw.rect(surface, theme.YELLOW, r,
                                 border_radius=20, width=2)
            btn.draw(surface, override_rect=r)

        self.device_apply_btn.draw(surface)

        # Right panel
        if not self.selected_device:
            hint = theme.FONT_SMALL.render(
                "Select a device to configure", True, theme.LIGHT_GRAY
            )
            surface.blit(hint, (self.sidebar_width + 40, CONTENT_Y + 30))
            return

        # Device name heading
        heading = theme.FONT_MEDIUM.render(
            self.selected_device, True, theme.BRIGHT_BLUE
        )
        surface.blit(heading, (self.sidebar_width + 40, CONTENT_Y + 12))

        # Unsaved indicator
        if self.unsaved_changes:
            dot = theme.FONT_SMALL.render("● unsaved changes", True, theme.YELLOW)
            surface.blit(dot, (self.sidebar_width + 40, CONTENT_Y + 46))

        # Settings widgets — label rendered at widget._label_y, widget below it
        open_dropdowns = []

        for key, widget in self.device_settings_widgets:
            label_text = ("Polling Frequency" if key == "poll_rate"
                        else key.replace("_", " ").title())
            label_y = getattr(widget, "_label_y", widget.rect.y - 24)
            lbl = theme.FONT_SMALL.render(label_text, True, theme.LIGHT_GRAY)
            surface.blit(lbl, (widget.rect.x, label_y))

            # Draw the widget normally
            widget.draw(surface)

            # If it's a dropdown and it's open, save it for later
            if isinstance(widget, DropDown) and widget.expanded:
                open_dropdowns.append(widget)

        # Draw open dropdown menus LAST so they appear on top
        for dd in open_dropdowns:
            dd.draw_expanded(surface)
