import json
from types import SimpleNamespace

import pygame
import ui.utilities as utilities

from ui import display_ui
from ui.control_ui import ControlUI
from ui.screens.AddScreen import AddScreen
from ui.screens.BaseScreen import BaseScreen
from ui.screens.EmailScreen import EmailScreen
from ui.screens.InitScreen import InitScreen
from ui.screens.MainScreen import MainScreen
from ui.screens.SettingsScreen import SettingsScreen, TAB_DEVICE, TAB_SYSTEM
from ui.screens.SystemDashboardScreen import SystemDashboardScreen
from ui.screens.WiFiScreen import WiFiScreen
from ui.widgets.ConfirmationPopup import ConfirmationPopup
from ui.widgets.SettingsPopup import SettingsPopup


def _surface(size=(40, 40)):
    return pygame.Surface(size, pygame.SRCALPHA)


def _patch_assets(monkeypatch):
    monkeypatch.setattr(
        BaseScreen,
        "load_assets",
        lambda self: setattr(
            self,
            "assets",
            {
                "power_button.png": _surface(),
                "trash.png": _surface(),
                "house.png": _surface(),
                "edit.png": _surface(),
            },
        ),
    )


class _UIControl:
    def __init__(self, bus):
        self.bus = bus
        self.stopped = 0
        self.simulate_brightness = 100
        self.sleep_enabled = False
        self.sleep_time = 30

    def preview_brightness(self, value):
        self.last_preview = value

    def set_brightness(self, value):
        self.last_brightness = value

    def change_polling_rate(self, host, new_rate):
        self.last_polling = (host, new_rate)

    def pause_polling(self, device_name, paused):
        self.last_pause = (device_name, paused)

    def change_device_name(self, old_name, new_name):
        self.last_rename = (old_name, new_name)

    def remove_node(self, device_name):
        self.last_remove = device_name

    def add_node(self, node_config):
        self.last_add = node_config

    def stop_system(self):
        self.stopped += 1

    def set_sleep_enabled(self, enabled):
        self.sleep_enabled = enabled

    def set_sleep_time(self, seconds):
        self.sleep_time = seconds

    def update_activity(self):
        return None

    def check_sleep(self):
        return None

    def get_dimming_alpha(self):
        return 0


def _app(fake_bus, temp_config):
    class DummyApp(SimpleNamespace):
        def change_screen(self, name):
            self.changed_screens.append(name)

    devices = [
        {
            "name": "alpha",
            "status": "Available",
            "polling_frequency": 15,
            "polling_paused": False,
            "stats": {"cpu": 1},
        },
        {
            "name": "beta",
            "status": "Offline",
            "polling_frequency": 30,
            "polling_paused": True,
            "stats": {},
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
    app.ui_control = _UIControl(fake_bus)
    return app


def test_control_ui_preview_brightness_on_pi(fake_bus, temp_config, monkeypatch):
    monkeypatch.setattr("builtins.open", lambda *_a, **_k: (_ for _ in ()).throw(FileNotFoundError()))
    ui = ControlUI(fake_bus, temp_config)
    ui.on_pi = True
    ui._save_ui_settings = lambda _settings: None
    ui.preview_brightness(33)
    assert ui.simulate_brightness == 33


def test_display_ui_remaining_paths(monkeypatch, tmp_path, fake_bus, temp_config, ui_surface):
    original_boot_router = display_ui.DisplayUI._boot_router
    class FakeMain:
        def __init__(self, app):
            self.selected_device = None
            self.build_calls = 0

        def _build_device_buttons(self):
            self.build_calls += 1

        def handle_event(self, event):
            pass

        def update(self):
            pass

        def draw(self, surface):
            surface.fill((0, 0, 0))

    class FakeSettings:
        def __init__(self, app):
            self.selected_device = "alpha"
            self.device_buttons = {"alpha": object()}
            self.pending_name_change = None
            self.build_list_calls = 0
            self.build_widget_calls = 0

        def _build_settings_widgets(self):
            self.build_widget_calls += 1
            # Force the duplicated selected-device branch in DisplayUI._handle_ack_update_name.
            self.selected_device = "alpha"

        def _build_device_list(self):
            self.build_list_calls += 1

        def _commit_name_change(self, old, new):
            self.selected_device = new

        def handle_event(self, event):
            pass

        def update(self):
            pass

        def draw(self, surface):
            surface.fill((1, 1, 1))

    class FakeSimple:
        def __init__(self, app):
            self.token_to_be_disp = False
            self.token = None

        def handle_event(self, event):
            pass

        def update(self):
            pass

        def draw(self, surface):
            surface.fill((2, 2, 2))

    monkeypatch.setattr(display_ui, "MainScreen", FakeMain)
    monkeypatch.setattr(display_ui, "SettingsScreen", FakeSettings)
    monkeypatch.setattr(display_ui, "SystemDashboardScreen", FakeSimple)
    monkeypatch.setattr(display_ui, "AddScreen", FakeSimple)
    monkeypatch.setattr(display_ui, "WiFiScreen", FakeSimple)
    monkeypatch.setattr(display_ui, "InitScreen", FakeSimple)
    monkeypatch.setattr(display_ui, "EmailScreen", FakeSimple)
    monkeypatch.setattr(display_ui.DisplayUI, "_boot_router", lambda self: "main")
    monkeypatch.setattr(pygame.display, "set_mode", lambda _size: ui_surface)
    monkeypatch.setattr(pygame.display, "set_caption", lambda _title: None)

    device_file = tmp_path / "devices.json"
    device_file.write_text(json.dumps({"alpha": {"name": "alpha"}}), encoding="utf-8")
    temp_config.decrypted_list = str(device_file)

    app = display_ui.DisplayUI(temp_config, bus=fake_bus, ui_control=_UIControl(fake_bus))

    app.current_screen = app.screens["settings"]
    app._handle_ack_update_name({"old_name": "alpha", "new_name": "omega"})
    assert app.current_screen.selected_device == "omega"

    app.current_screen = app.screens["main"]
    app._handle_ack_update_name({"old_name": "omega", "new_name": "zeta"})
    assert app.current_screen.build_calls >= 1

    app._handle_device_list_update({"n1": {"name": "n1"}})
    assert app.current_screen.build_calls >= 2

    monkeypatch.setattr(display_ui.DisplayUI, "_boot_router", original_boot_router)
    ui = display_ui.DisplayUI.__new__(display_ui.DisplayUI)
    ui.config = SimpleNamespace(ssh_key_enc="missing-key", dev_mode=False)
    monkeypatch.setattr(display_ui.os.path, "exists", lambda _p: False)
    monkeypatch.setattr(display_ui.subprocess, "run", lambda *_a, **_k: SimpleNamespace(stdout="20 (disconnected)"))
    assert ui._boot_router() == "wifi_setup"


def test_add_email_wifi_remaining_paths(monkeypatch, fake_bus, temp_config, ui_surface):
    _patch_assets(monkeypatch)
    app = _app(fake_bus, temp_config)

    add = AddScreen(app)
    add._on_key_pressed("x")

    add.active_textbox = add.passwordBox
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.DeviceNameBox.rect.center))
    add.active_textbox = add.DeviceNameBox
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.passwordBox.rect.center))
    add.active_textbox = add.passwordBox
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.UserNameBox.rect.center))

    email = EmailScreen(app)
    monkeypatch.setattr(email.keyboard, "handle_event", lambda _pos: True)
    email.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=email.save_btn.rect.center))
    email.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(1, 1)))

    import builtins

    original_open = builtins.open
    monkeypatch.setattr("builtins.open", lambda *_a, **_k: (_ for _ in ()).throw(OSError("boom")))
    email._save_settings(opt_out=False)
    monkeypatch.setattr("builtins.open", original_open)

    wifi = WiFiScreen(app)
    wifi.active_field = "password"
    wifi.on_key_press("x")
    wifi.on_key_press("Enter")
    wifi.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(1, 1)))
    monkeypatch.setattr(wifi.keyboard, "handle_event", lambda _pos: True)
    wifi.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=wifi.ssid_rect.center))


def test_init_screen_remaining_paths(monkeypatch, fake_bus, temp_config, ui_surface):
    app = _app(fake_bus, temp_config)

    # First boot instance
    s1 = InitScreen(app)
    s1.is_waiting = True
    s1.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=s1.buttons[0].rect.center))

    s1.is_waiting = False
    s1.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    s1.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(1, 1)))

    called = []
    s1._execute_script = lambda path=None: called.append(path)
    s1.passcode = "12345678"
    s1.is_confirming = False
    s1._handle_first_boot_logic()
    s1.passcode = "1234567"
    s1.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=s1.buttons[0].rect.center))
    s1.passcode = "00000000"
    s1.is_confirming = True
    s1.first_entry = "12345678"
    s1._handle_first_boot_logic()
    s1.passcode = "12345678"
    s1.is_confirming = True
    s1.first_entry = "12345678"
    s1._handle_first_boot_logic()
    assert called == ["./make_secrets.sh"]

    called.clear()
    s1._execute_script = lambda path=None: called.append(path)
    s1._handle_standard_unlock()
    assert called == ["./startup_script.sh"]

    s1._on_unlock_result({"success": True})
    assert "email_setup" in app.changed_screens

    # Standard boot instance
    key_path = temp_config.ssh_key_enc
    with open(key_path, "w", encoding="utf-8") as f:
        f.write("k")

    app2 = _app(fake_bus, temp_config)
    s2 = InitScreen(app2)

    # Cover handle_event branch that routes to standard unlock when passcode reaches 8 digits.
    called_unlock = []
    s2._handle_standard_unlock = lambda: called_unlock.append(True)
    s2.passcode = "1234567"
    s2.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=s2.buttons[0].rect.center))
    assert called_unlock == [True]

    # Missing email file -> email setup
    s2._on_unlock_result({"success": True})
    assert "email_setup" in app2.changed_screens

    # Bad email json -> email setup
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        f.write("{")
    s2._on_unlock_result({"success": True})

    # Completed email setup -> dashboard
    with open(temp_config.email_settings, "w", encoding="utf-8") as f:
        json.dump({"email_configured": True, "email_opt_out": False}, f)
    s2._on_unlock_result({"success": True})
    assert "dashboard" in app2.changed_screens

    # Failure path
    s2.passcode = "1111"
    s2._on_unlock_result({"success": False, "error": "bad"})
    assert s2.passcode == ""

    # Draw branches
    s2.is_first_boot = False
    s2.draw(ui_surface)
    s2.is_first_boot = True
    s2.is_confirming = True
    s2.is_waiting = True
    s2.draw(ui_surface)


def test_main_and_settings_remaining_paths(monkeypatch, tmp_path, fake_bus, temp_config, ui_surface):
    _patch_assets(monkeypatch)
    app = _app(fake_bus, temp_config)

    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache_data.json"
    app.config.cache_file = str(cache_path)
    cache_path.write_text(
        json.dumps({"alpha": {"timestamp": "2026-04-08T10:00:00.000", "metrics": {"uptime_seconds": 200000}, "severities": {}}}),
        encoding="utf-8",
    )

    main = MainScreen(app)
    main.metric_scrollbar_thumb_rect = None
    main.selected_device = app.devices[0]
    assert main._try_start_metric_scroll_drag(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1)), (1, 1)) is False

    main.metric_scrollbar_thumb_rect = pygame.Rect(10, 10, 8, 40)
    main.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(12, 20)))
    main.update()

    main.use_24hr = True
    main.sidebar.current_width = main.sidebar.width_expanded
    main.remove_mode = True
    main._build_remove_icons()
    main.popup = ConfirmationPopup(app, "x", lambda: None, lambda: None)
    main.device_scroll = 0
    main.draw(ui_surface)

    assert "d" in utilities.format_metric_value("uptime_seconds", 200000)
    main.metric_viewport_rect = None
    main._clamp_metric_scroll()
    main.metric_viewport_rect = pygame.Rect(100, 100, 300, 120)
    main.metric_content_height = 60
    main._draw_metric_scrollbar(ui_surface)
    assert main._get_metric_scrollbar_geometry() is None

    main.stat_buttons = {}
    main._layout_stat_buttons()

    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (900, 580))
    main.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))

    settings = SettingsScreen(app)
    settings.selected_device = None
    settings._build_settings_widgets()
    settings.selected_device = "missing"
    settings._build_settings_widgets()

    settings.unsaved_changes = False
    settings._apply_device()
    settings.selected_device = "missing"
    settings.unsaved_changes = True
    settings._apply_device()

    settings._commit_name_change("ghost", "ghost2")

    settings.device_buttons = {"new": settings.device_apply_btn}
    settings.pending_name_change = ("old", "new")
    settings._revert_name_change()

    settings.active_tab = TAB_SYSTEM
    settings._switch_tab(TAB_SYSTEM)

    applied = []
    settings._apply_system = lambda: applied.append("system")
    settings._pending_action = lambda: None
    settings._confirm_apply_and_run()
    assert applied == ["system"]

    settings.active_tab = TAB_DEVICE
    settings.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(10, 10)))

    settings.selected_device = "alpha"
    settings._build_settings_widgets()
    dropdown = next(w for k, w in settings.device_settings_widgets if k == "poll_rate")
    monkeypatch.setattr(dropdown, "handle_event", lambda _event: "Medium")
    settings.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=dropdown.rect.center))

    settings.name_keyboard = SimpleNamespace(handle_event=lambda _pos: True, draw=lambda _surf: None)
    settings.editing_name = True
    settings.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(900, 500)))

    settings.device_settings_widgets = []
    settings.selected_device = "alpha"
    settings._activate_custom_polling()

    settings.confirm_popup = ConfirmationPopup(app, "Long message " * 20, lambda: None, lambda: None)
    settings.unsaved_changes = True
    settings.active_tab = TAB_DEVICE
    settings._build_settings_widgets()
    settings.draw(ui_surface)


def test_dashboard_remaining_paths(monkeypatch, tmp_path, fake_bus, temp_config, ui_surface):
    _patch_assets(monkeypatch)
    app = _app(fake_bus, temp_config)

    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache_data.json"
    app.config.cache_file = str(cache_path)
    cache_path.write_text("{}", encoding="utf-8")

    # Cover fallback icon load path in __init__.
    monkeypatch.setattr(BaseScreen, "load_assets", lambda self: setattr(self, "assets", {}))

    class _Loaded:
        def convert_alpha(self):
            return _surface()

    monkeypatch.setattr("ui.screens.SystemDashboardScreen.pygame.image.load", lambda _p: _Loaded())
    monkeypatch.setattr(
        "ui.screens.SystemDashboardScreen.os.path.exists",
        lambda p: p.endswith("power_button.png") or p == app.config.cache_file,
    )

    s = SystemDashboardScreen(app)

    # JSON load failure path.
    monkeypatch.setattr("builtins.open", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("bad")))
    s._load_cache_data()

    s.cache_data = {"alpha": {"success": False, "metrics": {}}}
    assert s._get_device_status("alpha") == "Offline"
    s.cache_data = {"alpha": {"success": True, "metrics": {}}}
    assert s._get_device_status("alpha") == "Offline"
    s.cache_data = {"alpha": {"metrics": {"cpu_temp_c": None}}}
    assert s._calculate_aggregated_metrics()["cpu_temp_c"] is None

    s.selected_graph_device = None
    assert s._get_history_key() is None
    s.selected_graph_device = "alpha"
    s.cache_data = {"alpha": "bad"}
    assert s._get_history_key() is None

    s.app.devices = []
    s.cache_data = {}
    s._refresh_graph_device_selector()
    assert s.selected_graph_device is None

    assert s._get_selected_graph_metrics() is None
    s.selected_graph_device = "alpha"
    s.cache_data = {"alpha": "bad"}
    assert s._get_selected_graph_metrics() is None
    s.cache_data = {"alpha": {"metrics": "bad"}}
    assert s._get_selected_graph_metrics() is None

    s.metric_history = []
    s.selected_graph_device = None
    s._record_metric_history({})
    s._get_history_key = lambda: ("forced",)
    s._record_metric_history({})
    s.selected_graph_device = "alpha"
    s.cache_data = {"alpha": "bad"}
    s._record_metric_history({})
    s.cache_data = {"alpha": {"timestamp": "t", "metrics": {}}}
    s._record_metric_history({})

    # Selector-change branch + toggle branch.
    s.device_selector.options = ["alpha", "beta"]
    s.device_selector.selected = "alpha"
    s.selected_graph_device = "alpha"
    s.device_selector.handle_event = lambda _e: "beta"
    s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0)))
    assert s.selected_graph_device == "beta"

    s.device_selector.handle_event = lambda _e: None
    s.device_selector.rect = pygame.Rect(9999, 9999, 10, 10)
    s.network_toggle_button.rect = pygame.Rect(5, 5, 60, 30)
    s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=s.network_toggle_button.rect.center))

    # Draw/table/graph corner branches.
    s.cache_data = {"beta": {"metrics": {"cpu_load_1m": 0.5, "cpu_temp_c": None}}}
    s.selected_graph_device = None
    s.metric_history = [{"timestamp": "t1", "metrics": {"cpu_load_1m": 0.5}}, {"timestamp": "t2", "metrics": {"cpu_load_1m": 0.6}}]
    s.device_selector.expanded = True
    s._draw_metrics_graph(ui_surface, pygame.Rect(0, 0, 200, 160), {"cpu_load_1m": 0.5}, ["cpu_load_1m"])

    s.selected_graph_device = "beta"
    s.metric_history = [
        {"timestamp": "t1", "metrics": {"cpu_load_1m": None}},
        {"timestamp": "t2", "metrics": {"cpu_load_1m": 0.6}},
    ]
    s._draw_metrics_graph(ui_surface, pygame.Rect(0, 0, 90, 90), {"cpu_load_1m": 0.6}, ["cpu_load_1m"])

    big_averages = {k: 1.0 for k in s.METRIC_LABELS}
    big_averages["cpu_temp_c"] = None
    s._draw_metrics_table(ui_surface, pygame.Rect(0, 0, 220, 120), big_averages, ["cpu_load_1m"])

    # Cover None-point skip branch in graph loop.
    s._get_history_key = SystemDashboardScreen._get_history_key.__get__(s, SystemDashboardScreen)
    s.selected_graph_device = "beta"
    s.metric_history = [
        {"timestamp": "t1", "metrics": {"cpu_load_1m": None}},
        {"timestamp": "t2", "metrics": {"cpu_load_1m": 0.4}},
    ]
    s._draw_metrics_graph(ui_surface, pygame.Rect(0, 0, 360, 260), {"cpu_load_1m": 0.4}, ["cpu_load_1m"])

    scale_backup = s.GRAPH_SCALE_LIMITS.get("cpu_temp_c")
    s.GRAPH_SCALE_LIMITS["cpu_temp_c"] = 0.0
    assert s._normalize_metric_value("cpu_temp_c", 10) == 0.0
    s.GRAPH_SCALE_LIMITS["cpu_temp_c"] = scale_backup

    s._draw_averages_color_key(
        ui_surface,
        pygame.Rect(0, 0, 80, 20),
        ["cpu_load_1m", "cpu_temp_c", "mem_used_percent", "disk_used_percent"],
    )

    popup = SettingsPopup(app, pygame.Rect(980, 10, 40, 20))
    popup.close_popup()
    popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0)))
    popup.open_popup()
    popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=popup.system_btn.rect.center))
    popup.open_popup()
    popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=popup.device_btn.rect.center))
    popup.open_popup()
    popup.draw(ui_surface)

    # Sidebar animation snap branches.
    from ui.widgets.SidebarPanel import SidebarPanel

    sidebar = SidebarPanel(app, 0, 0, 220, 40, app.height, expanded=True)
    sidebar.current_width = 215
    sidebar.update()
    sidebar.expanded = False
    sidebar.current_width = 45
    sidebar.update()


def test_init_screen_first_boot_handle_event_branch(fake_bus, temp_config):
    app = _app(fake_bus, temp_config)
    s = InitScreen(app)
    assert s.is_first_boot is True

    hits = []
    s._handle_first_boot_logic = lambda: hits.append(True)
    s.passcode = "1234567"
    s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=s.buttons[0].rect.center))
    assert hits == [True]


def test_main_screen_drag_guard_and_sidebar_draw_lines(monkeypatch, tmp_path, fake_bus, temp_config, ui_surface):
    _patch_assets(monkeypatch)
    app = _app(fake_bus, temp_config)

    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache_data.json"
    app.config.cache_file = str(cache_path)
    cache_path.write_text("{}", encoding="utf-8")

    main = MainScreen(app)
    main.selected_device = app.devices[0]
    main.metric_scrollbar_thumb_rect = None
    assert main._try_start_metric_scroll_drag(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10)), (10, 10)) is False

    main.sidebar.current_width = main.sidebar.width_expanded
    main.device_scroll = 0
    main.selected_device = None

    draw_hits = []
    for btn in main.device_buttons:
        btn.draw = lambda _surface, override_rect=None, _hits=draw_hits: _hits.append(override_rect)

    main.draw(ui_surface)
    assert draw_hits

    # Force off-screen list items to hit the sidebar skip branch.
    main.device_scroll = -10000
    main.draw(ui_surface)

