import json
import os
from types import SimpleNamespace

import pygame

from ui import display_ui
from ui.control_ui import ControlUI
from ui.screens.AddScreen import AddScreen
from ui.screens.BaseScreen import BaseScreen
from ui.screens.EmailScreen import EmailScreen
from ui.screens.InitScreen import InitScreen
from ui.screens.WiFiScreen import WiFiScreen
from ui.utilities import dim_background, get_event_pos
from ui.widgets.Button import Button
from ui.widgets.ConfirmationPopup import ConfirmationPopup
from ui.widgets.DisplayPopup import DisplayPopup
from ui.widgets.Dropdown import DropDown
from ui.widgets.Keyboard import Keyboard
from ui.widgets.Numpad import Numpad
from ui.widgets.SettingsPopup import SettingsPopup
from ui.widgets.SidebarPanel import SidebarPanel
from ui.widgets.Slider import Slider
from ui.widgets.ToggleSwitch import ToggleSwitch


def test_utilities_and_button_smoke(ui_app, ui_surface):
    mouse_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 20))
    finger_event = pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.25)
    assert get_event_pos(mouse_event, ui_app) == (10, 20)
    assert get_event_pos(finger_event, ui_app) == (512, 150)
    assert get_event_pos(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a), ui_app) is None

    dim_background(ui_app, ui_surface)

    button = Button((0, 0, 100, 40), text="Very long text for fitting", bg_color=(1, 2, 3), border_color=(255, 255, 255), border_thickness=2)
    font, text = button._fit_text(button.text, 40)
    assert text
    button.draw(ui_surface)
    button.draw(ui_surface, override_rect=pygame.Rect(0, 50, 80, 30))
    assert button.is_clicked((5, 5)) is True
    assert button.is_clicked((500, 500)) is False


def test_slider_dropdown_toggle_keyboard_and_numpad(ui_app, ui_surface):
    changes = []
    slider = Slider(ui_app, (10, 10, 200, 20), default_value=10, on_change=lambda value: changes.append(int(value)))
    handle_center = slider._handle_rect().center
    slider.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=handle_center))
    slider.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(200, 20)))
    slider.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(200, 20)))
    slider.draw(ui_surface)
    assert slider.dragging is False
    assert changes

    dropdown = DropDown(ui_app, pygame.Rect(10, 40, 200, 40), ["A", "B", "C"])
    assert dropdown.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(20, 50))) is None
    selected = dropdown.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(20, 85)))
    dropdown.draw(ui_surface)
    dropdown.draw_expanded(ui_surface)
    assert selected in {None, "A", "B", "C"}

    toggled = []
    switch = ToggleSwitch(ui_app, (10, 100, 60, 30), default=False, on_change=lambda value: toggled.append(value))
    assert switch.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(20, 110))) is True
    switch.draw(ui_surface)
    assert toggled == [True]

    key_presses = []
    keyboard = Keyboard(0, 150, 600, key_presses.append)
    shift_btn = next(btn for btn in keyboard.buttons if btn.text in {"Shift", "shift"})
    keyboard.handle_event(shift_btn.rect.center)
    assert keyboard.mode == "upper"
    enter_btn = next(btn for btn in keyboard.buttons if btn.text == "Enter")
    keyboard.handle_event(enter_btn.rect.center)
    keyboard.draw(ui_surface)
    assert "Enter" in key_presses

    numpad_presses = []
    numpad = Numpad(0, 0, numpad_presses.append)
    assert numpad.handle_event(numpad.buttons[0].rect.center) is True
    assert numpad.handle_event((9999, 9999)) is False
    numpad.draw(ui_surface)
    assert numpad_presses


def test_popup_and_sidebar_smoke(ui_app, ui_surface):
    actions = []
    popup = ConfirmationPopup(ui_app, "Confirm?", lambda: actions.append("yes"), lambda: actions.append("no"))
    popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=popup.confirm_yes.rect.center))
    popup.draw(ui_surface)
    assert actions == ["yes"]

    popup2 = ConfirmationPopup(ui_app, "Confirm?", lambda: actions.append("yes2"), lambda: actions.append("no2"))
    popup2.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=popup2.confirm_no.rect.center))
    assert actions[-1] == "no2"

    display_popup = DisplayPopup(ui_app, "Token", lambda: actions.append("done"))
    display_popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=display_popup.confirm_done.rect.center))
    display_popup.draw(ui_surface)
    assert actions[-1] == "done"

    settings = SettingsPopup(ui_app, pygame.Rect(900, 10, 50, 30))
    settings.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=settings.system_btn.rect.center))
    settings.draw(ui_surface)
    assert "systemsettings" in ui_app.changed_screens

    settings2 = SettingsPopup(ui_app, pygame.Rect(900, 10, 50, 30))
    settings2.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=settings2.device_btn.rect.center))
    settings3 = SettingsPopup(ui_app, pygame.Rect(900, 10, 50, 30))
    settings3.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=settings3.cancel_btn.rect.center))
    assert "devicesettings" in ui_app.changed_screens
    assert settings3.open is False

    sidebar = SidebarPanel(ui_app, 0, 0, 200, 40, ui_app.height)
    sidebar.update()
    sidebar.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=sidebar.toggle_button.rect.center))
    sidebar.update()
    sidebar.draw(ui_surface)


def test_control_ui_smoke(fake_bus, temp_config, monkeypatch, tmp_path):
    monkeypatch.setattr(ControlUI, "is_raspberry_pi", lambda self: False)
    ui = ControlUI(fake_bus, temp_config)
    ui.change_polling_rate("host1", 5)
    ui.add_node({"name": "n1"})
    ui.remove_node("n1")
    ui.pause_polling("n1", True)
    ui.change_device_name("old", "new")
    ui.stop_system()
    ui.preview_brightness(20)
    ui.set_brightness(30)
    assert ui.simulate_brightness == 30

    backlight_dir = tmp_path / "backlight"
    backlight_dir.mkdir()
    (backlight_dir / "max_brightness").write_text("100", encoding="utf-8")
    ui.on_pi = True
    ui.backlight_path = str(backlight_dir)
    ui._write_brightness(40)
    assert (backlight_dir / "brightness").read_text(encoding="utf-8") == "40"


class DummyScreenForAssets(BaseScreen):
    pass


def test_base_screen_load_assets_smoke(monkeypatch, ui_app):
    screen = DummyScreenForAssets(ui_app)
    screen_folder = os.path.join("assets", screen.__class__.__name__.replace("Screen", "").lower())

    monkeypatch.setattr(os.path, "isdir", lambda path: path in {"assets", screen_folder})
    monkeypatch.setattr(os, "listdir", lambda path: ["one.png"] if path == "assets" else ["two.webp"])
    monkeypatch.setattr(os.path, "isfile", lambda path: True)
    monkeypatch.setattr(pygame.image, "load", lambda path: pygame.Surface((5, 5), pygame.SRCALPHA))

    screen.load_assets()
    screen.handle_event(None)
    screen.update()
    screen.draw(pygame.Surface((10, 10)))
    assert set(screen.assets.keys()) == {"one.png", "two.webp"}


def test_init_wifi_email_add_screens_smoke(monkeypatch, ui_app, ui_surface):
    init_screen = InitScreen(ui_app)
    first_button_center = init_screen.buttons[0].rect.center
    init_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=first_button_center))
    init_screen._execute_script()
    init_screen._on_unlock_result({"success": False, "error": "bad pass"})
    init_screen.draw(ui_surface)
    assert init_screen.passcode == ""
    assert init_screen.error_message == "bad pass"

    init_screen.is_first_boot = False
    with open(ui_app.config.email_settings, "w", encoding="utf-8") as f:
        json.dump({"email_configured": True, "email_opt_out": False}, f)
    init_screen._on_unlock_result({"success": True})
    assert "dashboard" in ui_app.changed_screens

    wifi = WiFiScreen(ui_app)
    wifi.on_key_press("a")
    wifi.on_key_press("Back")
    wifi._attempt_connection()
    wifi._handle_wifi_result({"success": False, "error": "bad wifi"})
    wifi.draw(ui_surface)
    assert wifi.error_message == "bad wifi"
    wifi._handle_wifi_result({"success": True})
    assert "updater" in ui_app.changed_screens

    email = EmailScreen(ui_app)
    email.on_key_press("a")
    email.on_key_press("Back")
    email.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=email.skip_btn.rect.center))
    email.draw(ui_surface)
    assert os.path.exists(ui_app.config.email_settings)
    assert "add_device" in ui_app.changed_screens

    monkeypatch.setattr(BaseScreen, "load_assets", lambda self: setattr(self, "assets", {}))
    add = AddScreen(ui_app)
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.Password_button.rect.center))
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.DeviceNameBox.rect.center))
    add._on_key_pressed("X")
    add.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=add.done_button.rect.center))
    add.draw(ui_surface)
    assert ui_app.ui_control.added


def test_display_ui_boot_router_and_dummy_screen(monkeypatch, ui_surface, temp_config):
    ds = display_ui.DummyScreen("demo")
    ds.handle_event(None)
    ds.update()
    ds.draw(ui_surface)

    ui = display_ui.DisplayUI.__new__(display_ui.DisplayUI)
    ui.config = temp_config

    # first boot in dev mode -> wifi setup
    temp_config.dev_mode = True
    temp_config.ssh_key_enc = "/tmp/missing-key-file"
    assert ui._boot_router() == "wifi_setup"

    # standard boot -> updater
    key_path = os.path.join(temp_config.storage_dir, "id_ed25519.enc")
    open(key_path, "wb").close()
    temp_config.ssh_key_enc = key_path
    assert ui._boot_router() == "updater"

    # first boot, prod mode, connected network -> updater
    os.remove(key_path)
    temp_config.dev_mode = False
    monkeypatch.setattr(display_ui.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="100 (connected)"))
    assert ui._boot_router() == "updater"

    # first boot, prod mode, nmcli exception -> wifi setup
    monkeypatch.setattr(display_ui.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nmcli bad")))
    assert ui._boot_router() == "wifi_setup"

