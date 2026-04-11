import json
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import mock_open

import pygame
import pytest

from ui import display_ui
from ui.control_ui import ControlUI
from ui.screens.AddScreen import AddScreen
from ui.screens.BaseScreen import BaseScreen
from ui.screens.MainScreen import MainScreen
from ui.screens.SettingsScreen import SettingsScreen, TAB_DEVICE, TAB_SYSTEM
from ui.screens.SystemDashboardScreen import SystemDashboardScreen
from ui.screens.WiFiScreen import WiFiScreen
from ui.screens.EmailScreen import EmailScreen
from ui.widgets.Button import Button
from ui.widgets.ConfirmationPopup import ConfirmationPopup
from ui.widgets.DisplayPopup import DisplayPopup
from ui.widgets.Dropdown import DropDown
from ui.widgets.Keyboard import Keyboard
from ui.widgets.SettingsPopup import SettingsPopup
from ui.widgets.SidebarPanel import SidebarPanel
from ui.widgets.Slider import Slider
from ui.widgets.ToggleSwitch import ToggleSwitch
from ui.widgets.Textbox import Textbox
import ui.utilities as utilities

def _surface(size=(40, 40)):
    return pygame.Surface(size, pygame.SRCALPHA)


def _asset_dict():
    return {
        "power_button.png": _surface(),
        "trash.png": _surface(),
        "house.png": _surface(),
        "edit.png": _surface(),
    }


class RecordingUIControl:
    def __init__(self, bus):
        self.bus = bus
        self.simulate_brightness = 100
        self.sleep_enabled = False
        self.sleep_time = 30
        self.previewed = []
        self.brightness = []
        self.polling = []
        self.paused = []
        self.renamed = []
        self.removed = []
        self.added = []
        self.stopped = 0

    def preview_brightness(self, value):
        self.simulate_brightness = value
        self.previewed.append(value)

    def set_brightness(self, value):
        self.simulate_brightness = value
        self.brightness.append(value)

    def set_sleep_enabled(self, enabled):
        self.sleep_enabled = enabled

    def set_sleep_time(self, seconds):
        self.sleep_time = seconds

    def change_polling_rate(self, host, new_rate):
        self.polling.append((host, new_rate))

    def pause_polling(self, device_name, paused):
        self.paused.append((device_name, paused))

    def change_device_name(self, old_name, new_name):
        self.renamed.append((old_name, new_name))

    def remove_node(self, device_name):
        self.removed.append(device_name)

    def add_node(self, node_config):
        self.added.append(node_config)

    def stop_system(self):
        self.stopped += 1

    def update_activity(self):
        return None

    def check_sleep(self):
        return None

    def get_dimming_alpha(self):
        return 0


@pytest.fixture
def rich_ui_app(fake_bus, temp_config):
    class DummyApp(SimpleNamespace):
        def change_screen(self, name):
            self.changed_screens.append(name)

    devices = [
        {
            "name": "alpha",
            "status": "Available",
            "polling_frequency": 15,
            "polling_paused": False,
            "stats": {"cpu": 1, "mem": 2},
        },
        {
            "name": "beta",
            "status": "Offline",
            "polling_frequency": 30,
            "polling_paused": True,
            "stats": {"disk": 3},
        },
    ]
    main_stub = SimpleNamespace(
        METRIC_ORDER=list(MainScreen.METRIC_ORDER),
        METRIC_NAMES=dict(MainScreen.METRIC_NAMES),
    )
    app = DummyApp(
        width=1024,
        height=600,
        bus=fake_bus,
        config=temp_config,
        devices=devices,
        changed_screens=[],
        temp_unit="C",
        screens={"main": main_stub},
    )
    app.ui_control = RecordingUIControl(fake_bus)
    return app


def _patch_assets(monkeypatch):
    monkeypatch.setattr(BaseScreen, "load_assets", lambda self: setattr(self, "assets", _asset_dict()))


def test_control_ui_error_and_detection_branches(fake_bus, temp_config, monkeypatch, tmp_path, capsys):
    cpuinfo = mock_open(read_data="Hardware\t: Raspberry Pi")
    monkeypatch.setattr("builtins.open", cpuinfo)
    ui = ControlUI(fake_bus, temp_config)
    assert ui.on_pi is True

    broken_path = tmp_path / "missing-backlight"
    ui.backlight_path = str(broken_path)
    ui._write_brightness(50)
    assert "Brightness error:" in capsys.readouterr().out

    class MissingOpen:
        def __call__(self, *args, **kwargs):
            raise FileNotFoundError

    monkeypatch.setattr("builtins.open", MissingOpen())
    assert ControlUI(fake_bus, temp_config).is_raspberry_pi() is False


def test_widget_branch_coverage(ui_surface, rich_ui_app):
    textbox = Textbox((10, 10, 100, 40), text="placeholder", title="Title")
    textbox.consume("7")
    textbox.handle_event((15, 15))
    textbox.draw(ui_surface)
    textbox.handle_event((500, 500))
    textbox.activate(False)
    textbox.draw(ui_surface)
    assert textbox.is_clicked((15, 15)) is True

    image_button = Button((0, 0, 40, 40), image=_surface(), bg_color=(1, 1, 1), border_color=(2, 2, 2), border_thickness=1)
    image_button.draw(ui_surface, override_rect=pygame.Rect(5, 5, 30, 30))
    left_button = Button((0, 50, 100, 30), text="left", align="left")
    left_button.draw(ui_surface)

    dropdown = DropDown(rich_ui_app, pygame.Rect(10, 100, 120, 30), ["A", "B"], default="A")
    assert dropdown.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)) is None
    dropdown.expanded = True
    assert dropdown.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(500, 500))) is None
    dropdown.draw(ui_surface)
    dropdown.draw_expanded(ui_surface)
    dropdown.expanded = True
    dropdown.draw_expanded(ui_surface)

    presses = []
    keyboard = Keyboard(0, 150, 700, presses.append)
    key_123 = next(btn for btn in keyboard.buttons if btn.text == "123")
    keyboard.handle_event(key_123.rect.center)
    key_abc = next(btn for btn in keyboard.buttons if btn.text == "ABC")
    keyboard.handle_event(key_abc.rect.center)
    key_space = next(btn for btn in keyboard.buttons if btn.text == "SPACE")
    keyboard.handle_event(key_space.rect.center)
    key_back = next(btn for btn in keyboard.buttons if btn.text == "Back")
    keyboard.handle_event(key_back.rect.center)
    assert keyboard.handle_event((9999, 9999)) is False
    keyboard.draw(ui_surface)
    assert presses == [" ", "Back"]

    slider_changes = []
    slider = Slider(rich_ui_app, (20, 360, 200, 20), label="Volume", on_change=slider_changes.append)
    finger_down = pygame.event.Event(pygame.FINGERDOWN, x=slider._handle_rect().centerx / rich_ui_app.width, y=slider._handle_rect().centery / rich_ui_app.height)
    slider.handle_event(finger_down)
    finger_move = pygame.event.Event(pygame.FINGERMOTION, x=0.2, y=0.5)
    slider.handle_event(finger_move)
    slider.handle_event(pygame.event.Event(pygame.FINGERUP, x=0.2, y=0.5))
    slider.draw(ui_surface)
    assert slider_changes

    toggle_values = []
    toggle = ToggleSwitch(rich_ui_app, (250, 360, 50, 24), default=True, on_change=toggle_values.append)
    assert toggle.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)) is None
    assert toggle.handle_event(pygame.event.Event(pygame.FINGERDOWN, x=toggle.rect.centerx / rich_ui_app.width, y=toggle.rect.centery / rich_ui_app.height)) is False
    assert toggle.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(999, 999))) is None
    toggle.draw(ui_surface)
    assert toggle_values == [False]

    popup_actions = []
    popup = ConfirmationPopup(rich_ui_app, "No action", lambda: popup_actions.append("yes"), lambda: popup_actions.append("no"))
    popup.draw(ui_surface)
    popup.open = False
    popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0)))
    popup.draw(ui_surface)
    assert popup_actions == []

    display_popup = DisplayPopup(rich_ui_app, "token", lambda: popup_actions.append("done"))
    display_popup.handle_event(pygame.event.Event(pygame.FINGERDOWN, x=display_popup.confirm_done.rect.centerx / rich_ui_app.width, y=display_popup.confirm_done.rect.centery / rich_ui_app.height))
    display_popup.draw(ui_surface)
    display_popup.open = False
    display_popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0)))
    assert popup_actions == ["done"]

    settings_popup = SettingsPopup(rich_ui_app, pygame.Rect(980, 10, 40, 20))
    settings_popup.close_popup()
    settings_popup.draw(ui_surface)
    settings_popup.open_popup()
    settings_popup.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    settings_popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=settings_popup.cancel_btn.rect.center))
    assert settings_popup.open is False

    sidebar = SidebarPanel(rich_ui_app, 0, 0, 200, 40, rich_ui_app.height, expanded=False)
    sidebar.current_width = 200
    sidebar.update()
    sidebar.handle_event(pygame.event.Event(pygame.FINGERDOWN, x=sidebar.toggle_button.rect.centerx / rich_ui_app.width, y=sidebar.toggle_button.rect.centery / rich_ui_app.height))
    sidebar.draw(ui_surface)
    assert sidebar.expanded is True


def test_add_wifi_email_extended_branches(monkeypatch, rich_ui_app, ui_surface):
    _patch_assets(monkeypatch)
    add = AddScreen(rich_ui_app)
    add.token_to_be_disp = True
    add.token = "abc123"
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(999, 999)))
    add.draw(ui_surface)
    assert isinstance(add.popup, DisplayPopup)

    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.Endpoint_button.rect.center))
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.Password_button.rect.center))
    add.DeviceNameBox.txt = "new-pass-node"
    add.HostNameBox.txt = "10.0.0.2"
    add.UserNameBox.txt = "pi"
    add.passwordBox.txt = "secret"
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.done_button.rect.center))
    assert add.is_pairing is True
    add.draw(ui_surface)
    add._on_device_list_updated({"id-1": {"name": "new-pass-node"}})
    assert add.is_pairing is False
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.passwordBox.rect.center))
    add._on_key_pressed("s")
    add._on_key_pressed("Back")
    add._on_key_pressed("Enter")
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.UserNameBox.rect.center))
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.HostNameBox.rect.center))
    add.active_textbox = add.HostNameBox
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=next(iter(add.keyboard.buttons)).rect.center))
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.back_button.rect.center))
    assert "main" in rich_ui_app.changed_screens
    add.end_token_disp()
    assert add.popup is None

    wifi = WiFiScreen(rich_ui_app)
    wifi.is_connecting = True
    wifi._attempt_connection()
    wifi.is_connecting = False
    wifi.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    wifi.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=wifi.ssid_rect.center))
    wifi.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=wifi.pass_rect.center))
    wifi.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=wifi.connect_btn.rect.center))
    wifi.draw(ui_surface)
    wifi.update()
    assert any(event == "WIFI_CONNECT_REQ" for event, _ in rich_ui_app.bus.published)

    email = EmailScreen(rich_ui_app)
    email.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    email.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=email.save_btn.rect.center))
    email.email = "person@example.com"
    email.on_key_press("Enter")
    email.draw(ui_surface)
    email.update()
    with open(rich_ui_app.config.email_settings, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["email_configured"] is True


def test_main_screen_behavior_and_helpers(monkeypatch, tmp_path, rich_ui_app, ui_surface):
    _patch_assets(monkeypatch)
    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache_data.json"
    rich_ui_app.config.cache_file = str(cache_path)
    cache_payload = {
        "alpha": {
            "timestamp": "2026-04-08T12:34:56.789",
            "metrics": {
                "cpu_load_1m": 0.25,
                "cpu_temp_c": 50.5,
                "mem_used_percent": 75.1,
                "disk_used_percent": 40.0,
                "mem_used_mb": 512,
                "mem_total_mb": 1024,
                "cpu_clock_mhz": 1500.0,
                "core_voltage_v": 1.2,
                "net_rx_kbps": 2400,
                "net_tx_kbps": 300,
                "uptime_seconds": 90061,
                "extra": 7,
            },
            "severities": {"cpu_temp_c": "warning", "extra": "critical"},
        },
        "beta": {"timestamp": "2026-04-08T12:35:00.000", "metrics": {"cpu_load_1m": 0.5}, "severities": {}},
    }
    cache_path.write_text(json.dumps(cache_payload), encoding="utf-8")

    screen = MainScreen(rich_ui_app)
    assert screen.cache_data["alpha"]["metrics"]["cpu_load_1m"] == 0.25

    monkeypatch.setattr("ui.screens.MainScreen.json.load", lambda fh: (_ for _ in ()).throw(ValueError("bad json")))
    screen._load_cache_data()
    assert screen.cache_data == {}
    monkeypatch.setattr("ui.screens.MainScreen.json.load", lambda fh: cache_payload)
    screen._load_cache_data()

    assert screen._event_pos(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)) is None
    assert screen._format_timestamp("2026-04-08T12:34:56.789") == "2026-04-08 12:34:56"
    assert screen._format_timestamp(123) == "123"
    assert utilities.format_metric_value("uptime_seconds", 125) == "0h 2m"
    assert utilities.format_metric_value("net_rx_kbps", 2000) == "2.00 Mbps"
    assert utilities.format_metric_value("net_tx_kbps", 300) == "300 kbps"
    assert utilities.format_metric_value("mem_used_mb", 512.9, metric_units=screen.METRIC_UNITS) == "512 MB"
    assert utilities.format_metric_value("cpu_load_1m", 0.1234) == "0.12"
    assert utilities.format_metric_value("cpu_temp_c", 51.2) == "51.2°C"
    assert utilities.format_metric_value("extra", 7) == "7"

    screen.draw(ui_surface)
    screen.selected_device = rich_ui_app.devices[0]
    screen._build_stat_buttons()
    screen._layout_stat_buttons()
    screen.draw(ui_surface)
    assert screen.metric_viewport_rect is not None

    screen.metric_scroll = 100
    screen._clamp_metric_scroll()
    assert screen.metric_scroll == 0
    screen.metric_scroll = -10000
    screen._clamp_metric_scroll()
    assert screen.metric_scroll <= 0
    screen.scroll_metrics(1)
    geom = screen._get_metric_scrollbar_geometry()
    assert geom is not None
    screen._draw_metric_scrollbar(ui_surface)
    thumb = screen.metric_scrollbar_thumb_rect
    assert screen._try_start_metric_scroll_drag(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=thumb.center), thumb.center) is True
    screen.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(thumb.centerx, thumb.centery + 15)))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=thumb.center))
    assert screen.metric_drag_active is False

    sidebar_events = []
    monkeypatch.setattr(screen.sidebar, "handle_event", lambda event: sidebar_events.append(event.type))
    screen.metric_drag_active = True
    screen.metric_drag_pointer_id = 1
    screen.handle_event(pygame.event.Event(pygame.FINGERMOTION, x=0.5, y=0.5, finger_id=2))
    assert pygame.FINGERMOTION in sidebar_events

    screen.popup = ConfirmationPopup(rich_ui_app, "Confirm", lambda: None, lambda: None)
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.popup.confirm_no.rect.center))
    assert screen.popup is None

    rich_ui_app.changed_screens.clear()
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.power_button.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.dashboard_button.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.settings_button.rect.center))
    before = screen.use_24hr
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.clock_button.rect.center))
    assert screen.use_24hr is (not before)
    assert rich_ui_app.ui_control.stopped == 1
    assert {"dashboard", "settings"}.issubset(set(rich_ui_app.changed_screens))

    screen.sidebar.current_width = screen.sidebar.width_expanded
    first_btn = screen.device_buttons[0]
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=first_btn.rect.center))
    assert screen.selected_device["name"] == "alpha"
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.remove_button.rect.center))
    assert screen.remove_mode is True
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.add_button.rect.center))
    assert "add_device" in rich_ui_app.changed_screens

    screen._build_remove_icons()
    icon = screen.remove_icons["alpha"]
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=icon.rect.center))
    assert isinstance(screen.popup, ConfirmationPopup)
    screen.popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.popup.confirm_yes.rect.center))
    assert rich_ui_app.ui_control.removed == ["alpha"]
    screen.popup = None

    stat_btn = next(iter(screen.stat_buttons.values()))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=stat_btn.rect.center))

    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (1, 1))
    old_scroll = screen.device_scroll
    screen.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
    assert screen.device_scroll >= old_scroll
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: screen.metric_viewport_rect.center)
    old_metric = screen.metric_scroll
    screen.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-1))
    assert screen.metric_scroll <= old_metric

    single = MainScreen(rich_ui_app)
    single.device_buttons = single.device_buttons[:1]
    single.scroll_devices(-100)
    assert single.device_scroll <= 0
    single.metric_viewport_rect = None
    single._draw_metric_scrollbar(ui_surface)
    single._set_metric_scroll_from_thumb_top(10)
    single.selected_device = None
    assert single._try_start_metric_scroll_drag(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0)), (0, 0)) is False
    single._layout_stat_buttons()
    single._build_stat_buttons()
    single._enter_remove_mode()
    single._exit_remove_mode()


def test_settings_screen_behavior_and_rendering(monkeypatch, rich_ui_app, ui_surface):
    _patch_assets(monkeypatch)
    screen = SettingsScreen(rich_ui_app)

    screen._on_brightness_change(70)
    assert rich_ui_app.ui_control.previewed[-1] == 70
    screen._apply_system()
    assert rich_ui_app.ui_control.brightness[-1] == 70

    assert screen._get_device("missing") is None
    assert screen._polling_label(30) == "Low"
    assert screen._polling_label(15) == "Medium"
    assert screen._polling_label(5) == "High"

    screen._build_device_list()
    screen.selected_device = "alpha"
    rich_ui_app.devices[0]["polling_frequency"] = 77
    screen._build_settings_widgets()
    assert screen.show_custom_textbox is True
    screen._deactivate_custom_polling()
    screen._activate_custom_polling()
    screen._start_name_edit()
    screen._on_name_key("X")
    screen._on_name_key("Back")
    screen.temp_name = "alpha-renamed"
    screen._on_name_key("Enter")
    assert screen.pending_name_change == ("alpha", "alpha-renamed")

    screen._build_settings_widgets()
    screen.show_custom_textbox = True
    screen.show_numpad = True
    screen._on_numpad_key("1")
    screen._on_numpad_key("DEL")
    screen.custom_textbox.txt = "100"
    screen._on_numpad_key("OK")
    screen.custom_textbox.txt = "2"
    screen._on_numpad_key("OK")
    assert screen.custom_error_message == "Must be 5-6000"
    screen.custom_textbox.txt = "abc"
    screen._on_numpad_key("OK")

    screen.unsaved_changes = True
    screen.pending_name_change = ("alpha", "alpha-new")
    for key, widget in screen.device_settings_widgets:
        if key == "poll_rate":
            widget.selected = "Medium"
        elif key == "polling_paused":
            widget.value = True
    screen._apply_device()
    assert screen.pending_polling_change is True
    screen.pending_polling_change = False
    screen._apply_device()
    assert rich_ui_app.ui_control.renamed[-1] == ("alpha", "alpha-new")

    screen.pending_name_change = ("alpha-new", "alpha-final")
    screen.selected_device = "alpha-new"
    screen._revert_name_change()
    assert screen.selected_device == "alpha-new"

    screen.active_tab = TAB_SYSTEM
    screen.system_unsaved = True
    screen._switch_tab(TAB_DEVICE)
    assert screen.confirm_popup is not None
    screen._discard_and_run()
    assert screen.active_tab == TAB_DEVICE
    screen.active_tab = TAB_DEVICE
    screen.unsaved_changes = True
    screen._switch_tab(TAB_SYSTEM)
    screen._confirm_apply_and_run()
    assert screen.active_tab == TAB_SYSTEM

    screen.active_tab = TAB_DEVICE
    screen.unsaved_changes = True
    screen._go_home()
    assert screen.confirm_popup is not None
    screen._discard_and_run()
    assert "main" in rich_ui_app.changed_screens

    screen.confirm_popup = ConfirmationPopup(rich_ui_app, "Confirm", lambda: None, lambda: None)
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.confirm_popup.confirm_no.rect.center))
    screen.confirm_popup = None

    slider_events = []
    monkeypatch.setattr(screen.brightness_slider, "handle_event", lambda event: slider_events.append(event.type))
    screen.active_tab = TAB_SYSTEM
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    assert slider_events == [pygame.KEYDOWN]
    screen.system_unsaved = True
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.system_apply_btn.rect.center))

    screen.active_tab = TAB_DEVICE
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.tab_system_btn.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.tab_device_btn.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.back_btn.rect.center))

    screen.selected_device = None
    first_device_btn = next(iter(screen.device_buttons.values()))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=first_device_btn.rect.center))
    assert screen.selected_device == "alpha-new"

    screen._build_settings_widgets()
    screen.edit_btn_rect = pygame.Rect(400, 100, 24, 24)
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.edit_btn_rect.center))
    assert screen.editing_name is True
    screen.editing_name = False
    screen.name_keyboard = Keyboard(0, 0, 300, lambda key: None)
    screen.editing_name = True
    key_pos = next(iter(screen.name_keyboard.buttons)).rect.center
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=key_pos))

    screen.editing_name = False
    screen._build_settings_widgets()
    poll_dropdown = next(widget for key, widget in screen.device_settings_widgets if key == "poll_rate")
    toggle = next(widget for key, widget in screen.device_settings_widgets if key == "polling_paused")
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=poll_dropdown.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(poll_dropdown.rect.x + 10, poll_dropdown.rect.bottom + poll_dropdown.option_height * 3 + 10)))
    screen.show_custom_textbox = True
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.custom_textbox.rect.center))
    assert screen.show_numpad is True
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=toggle.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.device_apply_btn.rect.center))

    screen.draw(ui_surface)
    screen.active_tab = TAB_SYSTEM
    screen.system_unsaved = True
    screen.draw(ui_surface)
    screen.active_tab = TAB_DEVICE
    screen.selected_device = None
    screen.draw(ui_surface)
    screen.selected_device = "alpha-new"
    screen._build_settings_widgets()
    poll_dropdown = next(widget for key, widget in screen.device_settings_widgets if key == "poll_rate")
    poll_dropdown.expanded = True
    screen.show_custom_textbox = True
    screen.show_numpad = True
    screen.custom_error_message = "err"
    screen.name_keyboard = Keyboard(0, 0, 300, lambda key: None)
    screen.editing_name = True
    screen.draw(ui_surface)


def test_system_dashboard_screen_behavior(monkeypatch, tmp_path, rich_ui_app, ui_surface):
    _patch_assets(monkeypatch)
    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache_data.json"
    rich_ui_app.config.cache_file = str(cache_path)
    cache_path.write_text(
        json.dumps(
            {
                "alpha": {
                    "timestamp": "2026-04-08T10:00:00.000",
                    "status": "online",
                    "success": True,
                    "metrics": {
                        "cpu_load_1m": 0.4,
                        "cpu_temp_c": 55.0,
                        "mem_used_percent": 63.0,
                        "disk_used_percent": 70.0,
                        "net_rx_kbps": 3000,
                        "net_tx_kbps": 800,
                    },
                },
                "beta": {
                    "timestamp": "2026-04-08T10:01:00.000",
                    "status": "offline",
                    "success": False,
                    "metrics": {},
                },
            }
        ),
        encoding="utf-8",
    )

    screen = SystemDashboardScreen(rich_ui_app)
    assert screen._get_device_status("missing") == "Offline"
    assert screen._get_device_status("beta") == "Offline"
    assert screen._get_device_status("alpha") == "Online"
    averages = screen._calculate_aggregated_metrics()
    assert averages["cpu_temp_c"] == 55.0
    assert screen._get_device_counts() == (2, 1, 1)
    assert screen._get_history_key() is not None
    screen._record_metric_history(averages)
    before = list(screen.metric_history)
    screen._record_metric_history(averages)
    assert screen.metric_history == before

    screen.metric_history = [
        {"timestamp": f"2026-04-08T10:{i:02d}:00.000", "metrics": averages}
        for i in range(screen.HISTORY_LIMIT + 2)
    ]
    screen._last_history_key = None
    screen._record_metric_history(averages)
    assert len(screen.metric_history) <= screen.HISTORY_LIMIT

    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.power_button.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.main_screen_button.rect.center))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=screen.network_toggle_button.rect.center))
    screen.handle_event(pygame.event.Event(pygame.FINGERDOWN, x=screen.network_toggle_button.rect.centerx / rich_ui_app.width, y=screen.network_toggle_button.rect.centery / rich_ui_app.height))
    screen.update()

    assert utilities.format_metric_value("net_rx_kbps", 1500) == "1.50 Mbps"
    assert utilities.format_metric_value("cpu_load_1m", 0.25) == "0.25"
    assert utilities.format_metric_value("cpu_temp_c", 42.5) == "42.5°C"
    assert screen._normalize_metric_value("cpu_temp_c", 50) == 0.5
    assert screen._normalize_metric_value("custom", -10) == 0.0
    assert screen._format_history_label(None) == ""
    assert screen._format_history_label("plain") == "plain"
    assert screen._format_history_label("2026-04-08T10:00:00.000") == "10:00:00"

    screen.draw(ui_surface)
    graph_metrics = screen._get_active_graph_metrics(averages)
    screen._draw_status_box(ui_surface, 0, 0, 100, 60, "L", "1", (1, 2, 3))
    screen._draw_metrics_table(ui_surface, pygame.Rect(0, 0, 300, 300), averages, graph_metrics)
    screen._draw_metrics_graph(ui_surface, pygame.Rect(0, 0, 400, 300), averages, graph_metrics)
    screen._draw_averages_color_key(ui_surface, pygame.Rect(0, 0, 100, 100), [])
    assert graph_metrics
    screen.show_network_lines = True
    assert screen._get_active_graph_metrics(averages)[-1] == "net_tx_kbps"
    screen.draw(ui_surface)
    screen._draw_network_summary(ui_surface, pygame.Rect(0, 0, 300, 80), averages)
    screen._draw_network_summary(ui_surface, pygame.Rect(0, 0, 300, 80), {"net_rx_kbps": None, "net_tx_kbps": None})
    screen.metric_history = [{"timestamp": "2026-04-08T10:00:00.000", "metrics": averages}]
    screen._draw_metrics_graph(ui_surface, pygame.Rect(0, 0, 120, 120), averages, graph_metrics)

    monkeypatch.setattr(BaseScreen, "load_assets", lambda self: setattr(self, "assets", {}))
    monkeypatch.setattr("ui.screens.SystemDashboardScreen.os.path.exists", lambda path: False)
    fallback = SystemDashboardScreen(rich_ui_app)
    fallback.cache_data = {}
    assert fallback._calculate_aggregated_metrics() is None
    fallback.draw(ui_surface)


def test_display_ui_init_handlers_and_run(monkeypatch, tmp_path, fake_bus, temp_config, ui_surface):
    class FakeEventBus:
        def __init__(self):
            self.started = False
            self.subscribed = []
            self.published = []

        def start(self):
            self.started = True

        def subscribe(self, event_type, handler):
            self.subscribed.append((event_type, handler))

        def publish(self, event_type, payload=None):
            self.published.append((event_type, payload))

    class FakeControlUI:
        def __init__(self, bus):
            self.bus = bus
            self.simulate_brightness = 100
            self.sleep_enabled = False
            self.sleep_time = 30

        def update_activity(self):
            return None

        def check_sleep(self):
            return None

        def get_dimming_alpha(self):
            return 0

    class FakeMainScreen:
        def __init__(self, app):
            self.app = app
            self.selected_device = {"name": "alpha"}
            self.exit_calls = 0
            self.build_calls = 0

        def _exit_remove_mode(self):
            self.exit_calls += 1

        def _build_device_buttons(self):
            self.build_calls += 1

        def handle_event(self, event):
            self.last_event = event.type

        def update(self):
            self.updated = True

        def draw(self, surface):
            surface.fill((0, 0, 0))
            self.drawn = True

    class FakeSettingsScreen:
        def __init__(self, app):
            self.app = app
            self.selected_device = "alpha"
            self.device_buttons = {"alpha": Button((0, 0, 10, 10), text="alpha")}
            self.pending_name_change = None
            self.pending_polling_change = False
            self.unsaved_changes = False
            self.build_list_calls = 0
            self.build_widget_calls = 0

        def _build_settings_widgets(self):
            self.build_widget_calls += 1

        def _build_device_list(self):
            self.build_list_calls += 1

        def _commit_name_change(self, old_name, new_name):
            self.selected_device = new_name
            self.pending_name_change = None

        def handle_event(self, event):
            self.last_event = event.type

        def update(self):
            self.updated = True

        def draw(self, surface):
            surface.fill((1, 1, 1))

    class FakeAddScreen:
        def __init__(self, app):
            self.app = app
            self.token_to_be_disp = False
            self.token = None

        def handle_event(self, event):
            self.last_event = event.type

        def update(self):
            self.updated = True

        def draw(self, surface):
            surface.fill((2, 2, 2))

    class FakeSimpleScreen(FakeAddScreen):
        pass

    monkeypatch.setattr(display_ui, "MainScreen", FakeMainScreen)
    monkeypatch.setattr(display_ui, "SystemDashboardScreen", FakeSimpleScreen)
    monkeypatch.setattr(display_ui, "SettingsScreen", FakeSettingsScreen)
    monkeypatch.setattr(display_ui, "AddScreen", FakeAddScreen)
    monkeypatch.setattr(display_ui, "WiFiScreen", FakeSimpleScreen)
    monkeypatch.setattr(display_ui, "InitScreen", FakeSimpleScreen)
    monkeypatch.setattr(display_ui, "EmailScreen", FakeSimpleScreen)
    monkeypatch.setattr(display_ui.DisplayUI, "_boot_router", lambda self: "main")
    monkeypatch.setattr(pygame.display, "set_mode", lambda size: ui_surface)
    monkeypatch.setattr(pygame.display, "set_caption", lambda title: None)

    tmp_list = tmp_path / "devices.json"
    tmp_list.write_text(json.dumps({"alpha": {"name": "alpha", "polling_frequency": 15, "polling_paused": False}}), encoding="utf-8")
    temp_config.decrypted_list = str(tmp_list)

    app = display_ui.DisplayUI(temp_config, bus=fake_bus, ui_control=RecordingUIControl(fake_bus))
    assert app.devices[0]["name"] == "alpha"
    app.change_screen("settings")
    assert isinstance(app.current_screen, FakeSettingsScreen)
    app.shutdown()
    app._handle_stop_system()
    assert app._running is False

    app.current_screen = app.screens["main"]
    app._handle_ack_remove({"node": "alpha", "success": True})
    assert app.current_screen.selected_device is None
    assert app.current_screen.exit_calls == 1
    app.current_screen.selected_device = "alpha"
    app._handle_ack_remove({"node": "alpha", "success": True})
    assert app.current_screen.selected_device is None

    app.current_screen = app.screens["settings"]
    app._on_ack_polling_paused({"device": "alpha", "paused": True})
    assert app.devices[0]["polling_paused"] is True
    assert app.current_screen.build_widget_calls >= 1

    app.current_screen.pending_name_change = ("alpha", "omega")
    app._on_ack_update_polling_rate({"host": "alpha", "poll_rate": 5})
    assert app.current_screen.selected_device == "omega"

    app.current_screen = app.screens["settings"]
    app.current_screen.pending_name_change = None
    app._on_ack_update_polling_rate({"host": "alpha", "poll_rate": 12})
    assert app.devices[0]["polling_frequency"] == 12

    app.current_screen = app.screens["main"]
    app._on_ack_update_polling_rate({"host": "alpha", "poll_rate": 22})
    assert app.current_screen.build_calls >= 1

    app.current_screen = app.screens["settings"]
    app._handle_ack_update_name({"old_name": "alpha", "new_name": "zeta"})
    assert app.devices[0]["name"] == "zeta"

    app._handle_device_list_update({"n1": {"name": "n1"}})
    assert app.devices == [{"name": "n1"}]
    app._handle_token_display("TOKEN123")
    assert app.screens["add_device"].token == "TOKEN123"

    modules_backup = {name: sys.modules.get(name) for name in ("event_bus", "control_ui")}
    fake_event_mod = ModuleType("event_bus")
    fake_event_mod.EventBus = FakeEventBus
    fake_control_mod = ModuleType("control_ui")
    fake_control_mod.ControlUI = FakeControlUI
    sys.modules["event_bus"] = fake_event_mod
    sys.modules["control_ui"] = fake_control_mod
    try:
        auto_app = display_ui.DisplayUI(temp_config)
    finally:
        for name, module in modules_backup.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    assert auto_app.bus.started is True

    auto_app.current_screen = auto_app.screens["main"]
    events = [[pygame.event.Event(pygame.QUIT)]]
    monkeypatch.setattr(pygame.event, "get", lambda: events.pop(0) if events else [])
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    quit_calls = []
    monkeypatch.setattr(pygame, "quit", lambda: quit_calls.append("quit"))
    monkeypatch.setattr(display_ui.sys, "exit", lambda: quit_calls.append("exit"))
    auto_app.run()
    assert quit_calls == ["quit", "exit"]
