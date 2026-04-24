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
        self._pending_backend_name = None
        self._pending_polling_rate_ack = False
        self._pending_polling_pause_ack = False
        self._original_polling_frequency = None
        self._original_polling_paused = False
        self.sidebar_width = 220
        self.scroll_offset = 0
        self.show_custom_textbox = False
        self.show_numpad = False
        self.custom_error_message = None
        self.editing_name = False
        self.name_keyboard = None
        self.temp_name = ""
        self.device_scroll = 0
        self.device_settings_height = 0
        self.original_visible_metrics = []

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
            border_radius=19,
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
        #   CONTENT_Y + 60  →  unsaved indicator (conditional)
        #   CONTENT_Y + 90  →  slider track
        #   slider_y + 110  →  temperature unit row
        #   toggle_y + 70   →  sleep row
        #   toggle_y + 180  →  Apply button
        #
        slider_x = app.width // 2 - 280
        slider_y = CONTENT_Y + 90
        slider_w = 560
        self.slider_x = slider_x

        self.brightness_slider = Slider(
            app,
            rect=(slider_x, slider_y, slider_w, 20),
            min_value=0,
            max_value=100,
            default_value=self.app.ui_control.simulate_brightness,
            label="Brightness",
            track_color=theme.BLUE,
            on_change=self._on_brightness_change,
        )
        self.brightness_value = self.app.ui_control.simulate_brightness
        self._saved_brightness = self.app.ui_control.simulate_brightness

        toggle_y = slider_y + 110
        self.temp_unit_toggle = ToggleSwitch(
            self.app,
            rect=(slider_x, toggle_y, 60, 32),
            default=getattr(self.app, "temp_unit", "C") == "F"
        )
        self._saved_temp_unit = getattr(self.app, "temp_unit", "C")

        # Sleep settings
        self.sleep_toggle = ToggleSwitch(
            self.app,
            rect=(slider_x, toggle_y + 70, 60, 32),
            default=self.app.ui_control.sleep_enabled
        )
        self.sleep_dropdown = DropDown(
            self.app,
            pygame.Rect(slider_x + 120, toggle_y + 70, 200, 40),
            ["30 seconds", "5 minutes", "10 minutes", "30 minutes", "1 hour", "2 hours"],
            default=self._sleep_time_label(self.app.ui_control.sleep_time),
        )
        self.sleep_dropdown._label_y = toggle_y + 46
        self.sleep_dropdown_visible = self.app.ui_control.sleep_enabled
        self._saved_sleep_enabled = self.app.ui_control.sleep_enabled
        self._saved_sleep_time = self.app.ui_control.sleep_time

        apply_w = 180
        self.system_apply_btn = Button(
            pygame.Rect(app.width // 2 - apply_w // 2, toggle_y + 180, apply_w, 42),
            text="Apply",
            bg_color=theme.DARK_GRAY,
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

    def _on_temp_unit_change(self, value):
        self.app.temp_unit = "F" if value else "C"
        self.system_unsaved = True

    def _on_sleep_toggle_change(self, value):
        self.app.ui_control.set_sleep_enabled(value)
        self.sleep_dropdown_visible = value
        self.system_unsaved = True

    def _on_sleep_time_change(self, label):
        seconds = self._sleep_time_seconds(label)
        self.app.ui_control.set_sleep_time(seconds)
        self.system_unsaved = True

    def _sleep_time_label(self, seconds):
        mapping = {
            30: "30 seconds",
            300: "5 minutes",
            600: "10 minutes",
            1800: "30 minutes",
            3600: "1 hour",
            7200: "2 hours"
        }
        return mapping.get(seconds, "30 seconds")

    def _sleep_time_seconds(self, label):
        mapping = {
            "30 seconds": 30,
            "5 minutes": 300,
            "10 minutes": 600,
            "30 minutes": 1800,
            "1 hour": 3600,
            "2 hours": 7200
        }
        return mapping.get(label, 30)

    def _apply_system(self):
        self._saved_brightness = self.brightness_value
        self._saved_temp_unit = self.app.temp_unit
        self._saved_sleep_enabled = self.app.ui_control.sleep_enabled
        self._saved_sleep_time = self.app.ui_control.sleep_time
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

    def _collect_widget_state(self):
        """Write all current widget values into the device dict without sending to backend."""
        if not self.selected_device:
            return
        device = self._get_device(self.selected_device)
        if not device:
            return

        visible_metrics = []
        for key, widget in self.device_settings_widgets:
            if key.startswith("visible_"):
                if widget.value:
                    visible_metrics.append(key[8:])
        device["visible_metrics"] = visible_metrics

    def _build_settings_widgets(self):
        """Rebuild right-panel widgets for the currently selected device."""
        self.device_settings_widgets = []
        self.device_scroll = 0

        self.show_custom_textbox = False
        self.show_numpad = False
        self.custom_error_message = None

        if not self.selected_device:
            return

        device = self._get_device(self.selected_device)
        if device is None:
            return
        panel_x = self.sidebar_width + 40

        FIRST_ROW_Y = CONTENT_Y + 80
        LABEL_H     = 26
        ROW_STRIDE  = 80

        row_y = FIRST_ROW_Y

        # ── Polling frequency row ──────────────────────────────────────────
        poll_seconds  = int(device.get("polling_frequency", 15))
        self._original_polling_frequency = poll_seconds
        self._original_polling_paused = bool(device.get("polling_paused", False))
        default_label = self._polling_label(poll_seconds)

        poll_dropdown = DropDown(
            self.app,
            pygame.Rect(panel_x, row_y + LABEL_H, 200, 40),
            ["Low", "Medium", "High", "Custom"],
            default=default_label,
        )
        poll_dropdown._label_y = row_y

        self.device_settings_widgets.append(("poll_rate", poll_dropdown))
        row_y += ROW_STRIDE

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

        # ── Visible Metrics rows ──────────────────────────────────────────
        if "visible_metrics" not in device:
            device["visible_metrics"] = list(self.app.screens["main"].METRIC_ORDER)

        self.original_visible_metrics = device["visible_metrics"].copy()

        for metric in self.app.screens["main"].METRIC_ORDER:
            toggle = ToggleSwitch(
                self.app,
                rect=(panel_x, row_y + LABEL_H, 60, 32),
                default=metric in device["visible_metrics"]
            )
            toggle._label_y = row_y
            self.device_settings_widgets.append(("visible_" + metric, toggle))
            row_y += ROW_STRIDE

        self.device_settings_height = row_y - FIRST_ROW_Y

    def _polling_label(self, seconds):
        reverse_map = {v: k for k, v in self.POLLING_MAP.items()}
        return reverse_map.get(int(seconds), "Custom")

    def _get_label_for_key(self, key):
        if key == "poll_rate":
            return "Polling Frequency"
        if key == "polling_paused":
            return "Pause Polling"
        if key.startswith("visible_"):
            metric = key[8:]
            return self.app.screens["main"].METRIC_NAMES.get(metric, metric.replace("_", " ").title())
        return key

    def _apply_device(self):
        if not self.unsaved_changes or not self.selected_device:
            return

        # Allow a fresh apply attempt if external logic already cleared pending state.
        if not self.pending_polling_change:
            self._pending_polling_rate_ack = False
            self._pending_polling_pause_ack = False
            device = self._get_device(self.selected_device)
            if device:
                self._original_polling_frequency = int(device.get("polling_frequency", 15))
                self._original_polling_paused = bool(device.get("polling_paused", False))

        # Flush all widget state to device dict first
        self._collect_widget_state()

        device = self._get_device(self.selected_device)
        if not device:
            return

        # Capture backend name once before anything mutates it
        backend_name = self.original_name if self.pending_name_change else self.selected_device
        selected_rate = None
        selected_paused = None

        for key, widget in self.device_settings_widgets:
            if key == "poll_rate":
                if widget.selected == "Custom":
                    try:
                        numeric = int(self.custom_textbox.txt) if self.show_custom_textbox else int(device.get("polling_frequency", 15))
                    except (TypeError, ValueError):
                        numeric = int(device.get("polling_frequency", 15))
                else:
                    numeric = self.POLLING_MAP.get(widget.selected, 15)
                selected_rate = int(numeric)

                if int(numeric) != int(self._original_polling_frequency):
                    self.app.ui_control.change_polling_rate(backend_name, int(numeric))
                    device["polling_frequency"] = int(numeric)
                    #self.app.bus.publish("SYNC_VAULT", {})
                    self._pending_polling_rate_ack = True
                else:
                    self._pending_polling_rate_ack = False

            if key == "polling_paused":
                selected_paused = bool(widget.value)
                if bool(widget.value) != bool(self._original_polling_paused):
                    self.app.ui_control.pause_polling(backend_name, widget.value)
                    device["polling_paused"] = widget.value
                    self.app.bus.publish("SYNC_VAULT", {})
                    self._pending_polling_pause_ack = True
                else:
                    self._pending_polling_pause_ack = False

        # Apply visible metrics immediately — no ack needed
        visible_metrics = [
            key[8:] for key, widget in self.device_settings_widgets
            if key.startswith("visible_") and widget.value
        ]
        device["visible_metrics"] = visible_metrics
        self.app.bus.publish("SYNC_VAULT", {})

        self.pending_polling_change = (self._pending_polling_rate_ack or self._pending_polling_pause_ack)

        if self.pending_polling_change:
            # Store backend name so ack handler can match correctly
            self._pending_backend_name = backend_name
            self.unsaved_changes = True
            return

        if selected_rate is not None:
            self._original_polling_frequency = int(selected_rate)
        if selected_paused is not None:
            self._original_polling_paused = bool(selected_paused)

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
            reordered = {}
            for name, btn in self.device_buttons.items():
                if name == old_name:
                    btn.text = new_name
                    reordered[new_name] = btn
                else:
                    reordered[name] = btn
            self.device_buttons = reordered

        self.selected_device = new_name
        self.original_name = new_name
        self.pending_name_change = None

        self.app.ui_control.change_device_name(old_name, new_name)
        self.app.bus.publish("SYNC_VAULT", {})

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
        self._pending_polling_rate_ack = False
        self._pending_polling_pause_ack = False

    def _clamp_device_scroll(self):
        max_scroll = max(0, self.device_settings_height - (self.app.height - CONTENT_Y))
        self.device_scroll = max(0, min(self.device_scroll, max_scroll))

    def _draw_device_scrollbar(self, surface):
        if not self.selected_device or self.device_settings_height <= (self.app.height - CONTENT_Y):
            return

        scrollbar_width = 8
        viewport_rect = pygame.Rect(self.sidebar_width, CONTENT_Y, self.app.width - self.sidebar_width, self.app.height - CONTENT_Y)
        scrollbar_x = viewport_rect.right - scrollbar_width
        scrollbar_height = viewport_rect.height
        max_scroll = max(0, self.device_settings_height - (self.app.height - CONTENT_Y))

        thumb_height = max(20, scrollbar_height * ((self.app.height - CONTENT_Y) / self.device_settings_height))
        thumb_y = (viewport_rect.y + (self.device_scroll / max(1, max_scroll)) * (scrollbar_height - thumb_height)
                   if max_scroll > 0 else viewport_rect.y)

        pygame.draw.rect(surface, theme.GRAY, (scrollbar_x, viewport_rect.y, scrollbar_width, scrollbar_height), border_radius=4)
        pygame.draw.rect(surface, theme.BLUE, (scrollbar_x, thumb_y, scrollbar_width, thumb_height), border_radius=4)

    # ══════════════════════════════════════════════════════════════════════
    # Tab switching
    # ══════════════════════════════════════════════════════════════════════

    def _switch_tab(self, tab):
        if tab == self.active_tab:
            return
        unsaved = self.system_unsaved if self.active_tab == TAB_SYSTEM else self.unsaved_changes
        if unsaved:
            self._pending_action = lambda: self._do_switch_tab(tab)
            msg = ("Apply settings before switching?"
                   if self.active_tab == TAB_SYSTEM
                   else "Apply changes before switching?")
            self._open_confirm(msg)
        else:
            self._do_switch_tab(tab)

    def _do_switch_tab(self, tab):
        self.active_tab = tab
        self.tab_system_btn.bg_color = theme.BLUE if tab == TAB_SYSTEM else theme.DARK_GRAY
        self.tab_device_btn.bg_color = theme.BLUE if tab == TAB_DEVICE else theme.DARK_GRAY
         # Dynamically rebuild the device list whenever the Device tab is opened
        if tab == TAB_DEVICE:
            self._build_device_list()
            
            # Safety check: if the previously selected device was deleted elsewhere, clear the right panel
            if self.selected_device not in self.device_buttons:
                self.selected_device = None
                self.device_settings_widgets = []
                self.show_custom_textbox = False
                self.show_numpad = False

    # ══════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════

    def _go_home(self):
        unsaved = self.system_unsaved if self.active_tab == TAB_SYSTEM else self.unsaved_changes
        if unsaved:
            self._pending_action = lambda: self.app.change_screen("main")
            msg = ("Apply settings before leaving?"
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
            self.app.ui_control.set_sleep_enabled(self._saved_sleep_enabled)
            self.app.ui_control.set_sleep_time(self._saved_sleep_time)
            self.sleep_toggle.value = self._saved_sleep_enabled
            self.sleep_dropdown_visible = self._saved_sleep_enabled
            self.sleep_dropdown.selected = self._sleep_time_label(self._saved_sleep_time)
            self.system_unsaved = False
        else:
            self._revert_name_change()
            device = self._get_device(self.selected_device)
            if device:
                device["visible_metrics"] = self.original_visible_metrics.copy()
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

        # Slider and system toggles need all event types (drag/motion)
        if self.active_tab == TAB_SYSTEM:
            self.brightness_slider.handle_event(event)
            result = self.temp_unit_toggle.handle_event(event)
            if result is not None:
                self._on_temp_unit_change(result)
            result = self.sleep_toggle.handle_event(event)
            if result is not None:
                self._on_sleep_toggle_change(result)
            if self.sleep_dropdown_visible:
                result = self.sleep_dropdown.handle_event(event)
                if result is not None:
                    self._on_sleep_time_change(result)

        # Scroll handling
        if event.type == pygame.MOUSEWHEEL and self.active_tab == TAB_DEVICE and self.selected_device:
            self.device_scroll -= event.y * 20
            self._clamp_device_scroll()

        if event.type == pygame.FINGERMOTION and self.active_tab == TAB_DEVICE and self.selected_device:
            self.device_scroll -= event.dy * 200
            self._clamp_device_scroll()

        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return

        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            return

        # ── Header (always use raw pos) ───────────────────────────────────
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

        # Edit button is drawn at fixed position — use raw pos
        if self.selected_device and hasattr(self, 'edit_btn_rect') and self.edit_btn_rect.collidepoint(pos):
            self._start_name_edit()
            return

        # Apply button is fixed position — use raw pos
        if self.device_apply_btn.is_clicked(pos):
            self._apply_device()
            return

        # Device selection buttons in sidebar — use raw pos
        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)
            if r.collidepoint(pos):
                self.selected_device = name
                self.original_name = name
                self._build_settings_widgets()
                return

        # Widget interactions — compensate for scroll by adjusting pos
        if self.selected_device:
            scrolled_pos = (pos[0], pos[1] + self.device_scroll)

            for key, widget in self.device_settings_widgets:
                # Handle each widget exactly once to avoid dropdown open/close double toggles.
                if hasattr(widget, 'handle_event_at'):
                    result = widget.handle_event_at(scrolled_pos)
                else:
                    original_y = widget.rect.y
                    widget.rect.y -= self.device_scroll
                    result = widget.handle_event(event)
                    widget.rect.y = original_y

                if result is None:
                    continue

                if key == "poll_rate":
                    if result == "Custom":
                        self._activate_custom_polling()
                    else:
                        self._deactivate_custom_polling()
                elif key.startswith("visible_"):
                    device = self._get_device(self.selected_device)
                    if device:
                        device[key] = result
                self.unsaved_changes = True

            # Custom textbox / numpad
            if self.show_custom_textbox:
                if self.custom_textbox.rect.collidepoint(scrolled_pos):
                    self.show_numpad = True

            if self.show_numpad:
                self.numpad.handle_event(scrolled_pos)

        # Name keyboard (drawn fixed, use raw pos)
        if self.editing_name and self.name_keyboard:
            if self.name_keyboard.handle_event(pos):
                return

    def _activate_custom_polling(self):
        dropdown_rect = None
        for key, widget in self.device_settings_widgets:
            if key == "poll_rate":
                dropdown_rect = widget.rect
                break

        if dropdown_rect is None:
            dropdown_rect = pygame.Rect(400, 200, 200, 40)

        self.custom_textbox = Textbox(
            rect=pygame.Rect(dropdown_rect.right + 40, dropdown_rect.y, 150, 40),
            text="",
            title="Custom Polling"
        )

        self.numpad = Numpad(
            x=self.custom_textbox.rect.right + 20,
            y=self.custom_textbox.rect.y,
            callback=self._on_numpad_key
        )

        self.show_custom_textbox = True
        self.show_numpad = False

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
                self._collect_widget_state()  # save widget state before name edit commits
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
                    self.unsaved_changes = True
                    self.custom_error_message = None
                else:
                    self.custom_textbox.txt = str(device.get("polling_frequency", 15))
                    self.custom_error_message = "Must be 5-6000"
            except ValueError:
                self.custom_textbox.txt = str(device.get("polling_frequency", 15))
                self.custom_error_message = "Must be 5-6000"
            self.show_numpad = False
            return
        else:
            self.custom_textbox.consume(key)

    def on_polling_ack(self, device_name, kind):
        """Handle polling ACKs so Apply state clears only after all pending changes finish."""
        if self._pending_backend_name and device_name != self._pending_backend_name:
            return

        if kind == "rate":
            self._pending_polling_rate_ack = False
        elif kind == "pause":
            self._pending_polling_pause_ack = False

        self.pending_polling_change = (self._pending_polling_rate_ack or self._pending_polling_pause_ack)
        if self.pending_polling_change:
            return

        self._pending_backend_name = None

        if self.pending_name_change:
            old_name, new_name = self.pending_name_change
            self._commit_name_change(old_name, new_name)

        device = self._get_device(self.selected_device)
        if device:
            self._original_polling_frequency = int(device.get("polling_frequency", 15))
            self._original_polling_paused = bool(device.get("polling_paused", False))

        self.unsaved_changes = False

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

        if self.system_unsaved:
            dot = theme.FONT_SMALL.render("● unsaved changes", True, theme.YELLOW)
            surface.blit(dot, (self.app.width // 2 - dot.get_width() // 2,
                            CONTENT_Y + 46))

        self.brightness_slider.draw(surface)

        # ── Temperature unit row ──────────────────────────────────────────
        is_fahrenheit = self.app.temp_unit == "F"
        c_lbl = theme.FONT_SMALL.render("°C", True, theme.WHITE if not is_fahrenheit else theme.LIGHT_GRAY)
        f_lbl = theme.FONT_SMALL.render("°F", True, theme.WHITE if is_fahrenheit else theme.LIGHT_GRAY)
        row_label = theme.FONT_SMALL.render("Temperature Unit", True, theme.LIGHT_GRAY)

        toggle_y = self.temp_unit_toggle.rect.y
        toggle_h = self.temp_unit_toggle.rect.height

        surface.blit(row_label, (self.slider_x, toggle_y - 24))
        surface.blit(c_lbl, (self.slider_x, toggle_y + (toggle_h - c_lbl.get_height()) // 2))

        self.temp_unit_toggle.rect.x = self.slider_x + c_lbl.get_width() + 10
        self.temp_unit_toggle.draw(surface)

        f_y = toggle_y + (toggle_h - f_lbl.get_height()) // 2
        surface.blit(f_lbl, (self.temp_unit_toggle.rect.right + 10, f_y))

        # ── Sleep row ─────────────────────────────────────────────────────
        sleep_toggle_y = toggle_y + 70
        surface.blit(theme.FONT_SMALL.render("Enable Sleep", True, theme.LIGHT_GRAY),
                     (self.slider_x, sleep_toggle_y - 24))
        self.sleep_toggle.rect.x = self.slider_x
        self.sleep_toggle.rect.y = sleep_toggle_y
        self.sleep_toggle.draw(surface)

        if self.sleep_dropdown_visible:
            surface.blit(theme.FONT_SMALL.render("Sleep After", True, theme.LIGHT_GRAY),
                         (self.slider_x + 120, self.sleep_dropdown._label_y))
            self.sleep_dropdown.draw(surface)

        # Apply button
        self.system_apply_btn.bg_color = (theme.GREEN if self.system_unsaved
                                          else theme.DARK_GRAY)
        self.system_apply_btn.draw(surface)

        # Draw expanded sleep dropdown on top of everything
        if self.sleep_dropdown_visible:
            self.sleep_dropdown.draw_expanded(surface)

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
        current_display_name = self.pending_name_change[1] if self.pending_name_change else self.selected_device
        heading = theme.FONT_MEDIUM.render(current_display_name, True, theme.BRIGHT_BLUE)
        surface.blit(heading, (self.sidebar_width + 40, CONTENT_Y + 12))

        # Edit button
        if "edit.png" in self.assets:
            edit_icon = pygame.transform.smoothscale(self.assets["edit.png"], (24, 24))
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

        # Settings widgets
        open_dropdowns = []
        viewport = pygame.Rect(self.sidebar_width, CONTENT_Y,
                               self.app.width - self.sidebar_width,
                               self.app.height - CONTENT_Y)

        for key, widget in self.device_settings_widgets:
            label_text = self._get_label_for_key(key)
            label_y = getattr(widget, "_label_y", widget.rect.y - 24) - self.device_scroll

            if HEADER_H + 20 < label_y < self.app.height:
                lbl = theme.FONT_SMALL.render(label_text, True, theme.WHITE)
                surface.blit(lbl, (widget.rect.x, label_y))

            original_y = widget.rect.y
            widget.rect.y -= self.device_scroll
            if widget.rect.y > HEADER_H + 20 and widget.rect.colliderect(viewport):
                widget.draw(surface)
            widget.rect.y = original_y

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
            name_text = theme.FONT_MEDIUM.render(f"New Name: {self.temp_name}", True, theme.WHITE)
            surface.blit(name_text, (self.app.width // 2 - name_text.get_width() // 2, 250))

        # Draw open dropdowns on top
        for dd in open_dropdowns:
            dd.rect.y -= self.device_scroll
            dd.draw_expanded(surface)
            dd.rect.y += self.device_scroll

        self._draw_device_scrollbar(surface)