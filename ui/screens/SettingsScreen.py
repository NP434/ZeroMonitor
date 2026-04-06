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
from ui.widgets.Textbox import Textbox
from ui.widgets.Numpad import Numpad
from ui.widgets.Keyboard import Keyboard
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
        self.original_name = None
        self.device_buttons = {}
        self.device_settings_widgets = []
        self.unsaved_changes = False
        self.pending_name_change = None
        self.pending_polling_change = False
        self.sidebar_width = 220
        self.scroll_offset = 0
        self.show_custom_textbox = False
        self.show_numpad = False
        self.custom_error_message = None
        self.editing_name = False
        self.name_keyboard = None
        self.temp_name = ""


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

        toggle_y = slider_y + 110
        self.temp_unit_toggle = ToggleSwitch(
            self.app,
            rect=(150, toggle_y, 60, 32),
            default=False  # False = Celsius, True = Fahrenheit
        )
        self.temp_unit_label = "°C / °F"

    # ══════════════════════════════════════════════════════════════════════
    # System tab
    # ══════════════════════════════════════════════════════════════════════

    def _on_brightness_change(self, value):
        self.brightness_value = value
        self.system_unsaved = (round(value) != round(self._saved_brightness))
        self.app.ui_control.preview_brightness(value)

    def _on_temp_unit_change(self, value):
        self.app.temp_unit = "F" if value else "C"
        self.system_unsaved = True

    def _apply_system(self):
        self._saved_brightness = self.brightness_value
        self._saved_temp_unit = self.app.temp_unit
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

        self.show_custom_textbox = False
        self.show_numpad = False
        self.custom_error_message = None

        if not self.selected_device:
            return

        device = self._get_device(self.selected_device)
        if device is None:
            return
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
            ["Low", "Medium", "High", "Custom"],
            default=default_label,
        )
        poll_dropdown._label_y = row_y   # draw() uses this for the label

        self.device_settings_widgets.append(("poll_rate", poll_dropdown))
        row_y += ROW_STRIDE

        # If custom, activate the textbox
        if default_label == "Custom":
            self._activate_custom_polling()

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
        if not device:
            return

        # Determine backend identity for REST actions
        backend_name = self.original_name if self.pending_name_change else self.selected_device

        # Apply polling + pause updates
        has_polling_update = False

        for key, widget in self.device_settings_widgets:
            if key == "poll_rate":
                if widget.selected == "Custom":
                    numeric = device.get("polling_frequency", 15)
                else:
                    numeric = self.POLLING_MAP.get(widget.selected, 15)

                if numeric != device.get("polling_frequency", 15):
                    has_polling_update = True
                    self.app.ui_control.change_polling_rate(backend_name, numeric)
                    device["polling_frequency"] = numeric

            if key == "polling_paused":
                if widget.value != device.get("polling_paused", False):
                    has_polling_update = True
                    self.app.ui_control.pause_polling(backend_name, widget.value)
                    device["polling_paused"] = widget.value

        self.pending_polling_change = has_polling_update

        # If the name is pending and there is a polling update, keep it pending until poll ack.
        if self.pending_polling_change:
            self.unsaved_changes = True
            return

        # Execute device rename now if pending
        if self.pending_name_change:
            old_name, new_name = self.pending_name_change
            self._commit_name_change(old_name, new_name)

        self.unsaved_changes = False

    def _commit_name_change(self, old_name, new_name):
        device = self._get_device(old_name)
        if not device:
            return

        device["name"] = new_name

        if old_name in self.device_buttons:
            btn = self.device_buttons.pop(old_name)
            btn.text = new_name
            self.device_buttons[new_name] = btn

        self.selected_device = new_name
        self.original_name = new_name
        self.pending_name_change = None

        self.app.ui_control.change_device_name(old_name, new_name)

    def _revert_name_change(self):
        if not self.pending_name_change:
            return

        old_name, new_name = self.pending_name_change

        self.selected_device = old_name
        device = self._get_device(old_name)
        if device:
            device["name"] = old_name

        if new_name in self.device_buttons:
            btn = self.device_buttons.pop(new_name)
            btn.text = old_name
            self.device_buttons[old_name] = btn

        self.pending_name_change = None
        self.pending_polling_change = False

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
            self.app.temp_unit = self._saved_temp_unit
            self.temp_unit_toggle.value = (self._saved_temp_unit == "F")
            self.system_unsaved = False
        else:
            self._revert_name_change()
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

            result = self.temp_unit_toggle.handle_event(event)
            if result is not None:
                self._on_temp_unit_change(result)
            if self.system_unsaved and self.system_apply_btn.is_clicked(event.pos):
                self._apply_system()
            return

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
        # Device selection
        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)
            if r.collidepoint(pos):
                self.selected_device = name
                self.original_name = name
                self._build_settings_widgets()
                return

        # Widget interactions
        if self.selected_device:
            for key, widget in self.device_settings_widgets:
                result = widget.handle_event(event)

                # If nothing happens
                if result is None:
                    continue
                
                # If widget is the poll_rate widget
                if key == "poll_rate":
                    if result == "Custom":
                        self._activate_custom_polling()
                        continue
                    else:
                        self._deactivate_custom_polling()

                # Normal data collection from widgets
                device = self._get_device(self.selected_device)
                device[key] = result
                self.unsaved_changes = True
        
        # Edit name button
        if hasattr(self, 'edit_btn_rect') and self.edit_btn_rect.collidepoint(pos) and self.selected_device:
            self._start_name_edit()
            return

        # If custom textbox is visible, check if user clicked it
        if self.show_custom_textbox:
            if self.custom_textbox.rect.collidepoint(pos):
                self.show_numpad = True
            else:
                pass

        # Handle numpad events if visible
        if self.show_numpad:
            self.numpad.handle_event(pos)

        # Handle name keyboard
        if self.editing_name and self.name_keyboard:
            if self.name_keyboard.handle_event(pos):
                return

        if self.device_apply_btn.is_clicked(pos):
            self._apply_device()

    def _activate_custom_polling(self):
        # Find dropdown rect
        dropdown_rect = None
        for key, widget in self.device_settings_widgets:
            if key == "poll_rate":
                dropdown_rect = widget.rect
                break

        if dropdown_rect is None:
            dropdown_rect = pygame.Rect(400, 200, 200, 40)

        # Create textbox if needed
        self.custom_textbox = Textbox(
            rect=pygame.Rect(dropdown_rect.right + 40, dropdown_rect.y, 150, 40),
            text="",
            title="Custom Polling"
        )

        # Create numpad if needed
        self.numpad = Numpad(
            x=self.custom_textbox.rect.right + 20,
            y=self.custom_textbox.rect.y,
            callback=self._on_numpad_key
        )

        self.show_custom_textbox = True
        self.show_numpad = False 

        # Set textbox to current value
        device = self._get_device(self.selected_device)
        current_seconds = device.get("polling_frequency", 15)
        self.custom_textbox.txt = str(current_seconds)
        self.custom_error_message = None 


    def _deactivate_custom_polling(self):
        self.show_custom_textbox = False
        self.show_numpad = False
        self.custom_error_message = None

    def _start_name_edit(self):
        self.editing_name = True
        self.temp_name = self.selected_device
        self.name_keyboard = Keyboard(x=50, y=320, width=924, callback=self._on_name_key)

    def _on_name_key(self, key):
        if key == "Back":
            self.temp_name = self.temp_name[:-1]
        elif key == "Enter":
            new_name = self.temp_name.strip()
            old_name = self.selected_device
            if new_name and new_name != old_name:
                self.pending_name_change = (old_name, new_name)
                self.temp_name = new_name
                self.unsaved_changes = True
            self._end_name_edit()
        else:
            self.temp_name += key

    def _end_name_edit(self):
        self.editing_name = False
        self.name_keyboard = None

    def _on_numpad_key(self, key):
        if key == "DEL":
            self.custom_textbox.txt = self.custom_textbox.txt[:-1]
        elif key == "OK":
            device = self._get_device(self.selected_device)
            try:
                val = int(self.custom_textbox.txt)
                if 5 <= val <= 6000:
                    device["polling_frequency"] = val
                    self.unsaved_changes = True
                    self.custom_error_message = None
                else:
                    # Invalid range, reset to current value
                    self.custom_textbox.txt = str(device.get("polling_frequency", 15))
                    self.custom_error_message = "Must be 5-6000"
            except ValueError:
                # Invalid input, reset to current value
                self.custom_textbox.txt = str(device.get("polling_frequency", 15))
                self.custom_error_message = "Must be 5-6000"
            self.show_numpad = False
            return
        else:
            # Append digit
            self.custom_textbox.consume(key)

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

        # Temperature unit
        lbl = theme.FONT_SMALL.render("Temperature Unit  °C", True, theme.LIGHT_GRAY)
        surface.blit(lbl, (self.app.width // 2 - 30, self.temp_unit_toggle.rect.y - 24))
        self.temp_unit_toggle.draw(surface)
        f_lbl = theme.FONT_SMALL.render("°F", True, theme.LIGHT_GRAY)
        surface.blit(f_lbl, (self.app.width // 2 + 40, self.temp_unit_toggle.rect.y))

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

        if self.show_custom_textbox:
            self.custom_textbox.draw(surface)

        self.device_apply_btn.draw(surface)

        # Right panel
        if not self.selected_device:
            hint = theme.FONT_SMALL.render(
                "Select a device to configure", True, theme.LIGHT_GRAY
            )
            surface.blit(hint, (self.sidebar_width + 40, CONTENT_Y + 30))
            return

        # Device name heading (show pending name if queued)
        current_display_name = self.pending_name_change[1] if self.pending_name_change else self.selected_device
        heading = theme.FONT_MEDIUM.render(
            current_display_name, True, theme.BRIGHT_BLUE
        )
        surface.blit(heading, (self.sidebar_width + 40, CONTENT_Y + 12))

        # Edit button
        if "edit.png" in self.assets:
            edit_icon = pygame.transform.smoothscale(self.assets["edit.png"], (24, 24))
            # Make the icon white
            white_icon = pygame.Surface(edit_icon.get_size(), pygame.SRCALPHA)
            white_icon.fill((255, 255, 255, 255))
            white_icon.blit(edit_icon, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            edit_x = self.sidebar_width + 40 + heading.get_width() + 10
            edit_y = CONTENT_Y + 12
            surface.blit(white_icon, (edit_x, edit_y))
            self.edit_btn_rect = pygame.Rect(edit_x, edit_y, 24, 24)

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
        
        if self.show_custom_textbox:
            self.custom_textbox.draw(surface)
        if self.show_numpad:
            self.numpad.draw(surface)

        if self.custom_error_message:
            error_surf = theme.FONT_SMALL.render(self.custom_error_message, True, theme.RED)
            surface.blit(error_surf, (self.custom_textbox.rect.x, self.custom_textbox.rect.bottom + 5))

        if self.editing_name and self.name_keyboard:
            self.name_keyboard.draw(surface)
            # Draw current temp name
            name_text = theme.FONT_MEDIUM.render(f"New Name: {self.temp_name}", True, theme.WHITE)
            surface.blit(name_text, (self.app.width // 2 - name_text.get_width() // 2, 250))

        # Draw open dropdown menus LAST so they appear on top
        for dd in open_dropdowns:
            dd.draw_expanded(surface)
