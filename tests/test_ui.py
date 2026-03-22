import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()
import types
import sys

from update_checker_pkg import ui


class FakeSignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def fire(self):
        for callback in list(self._callbacks):
            callback(False)


class FakeAction:
    def __init__(self, text="", parent=None, name="", visible=True, enabled=True, menu_obj=None):
        self._text = text
        self._name = name
        self._visible = visible
        self._enabled = enabled
        self._tooltip = ""
        self._menu_obj = menu_obj
        self.triggered = FakeSignal()

    def objectName(self):
        return self._name

    def setObjectName(self, value):
        self._name = value

    def text(self):
        return self._text

    def setToolTip(self, value):
        self._tooltip = value

    def isVisible(self):
        return self._visible

    def isEnabled(self):
        return self._enabled

    def menu(self):
        return self._menu_obj


class FakeSubMenu:
    def __init__(self, text="", parent=None):
        self._text = text
        self._name = ""
        self._actions = []
        self._menu_action = FakeAction(text=text, parent=parent, menu_obj=self)

    def setObjectName(self, value):
        self._name = value

    def objectName(self):
        return self._name

    def addAction(self, action):
        self._actions.append(action)

    def actions(self):
        return list(self._actions)

    def menuAction(self):
        return self._menu_action


class FakeMenu:
    def __init__(self, actions=None):
        self._actions = list(actions or [])
        self.insertions = []
        self.separator_count = 0

    def actions(self):
        return list(self._actions)

    def insertAction(self, anchor, action):
        idx = self._actions.index(anchor)
        self._actions.insert(idx, action)
        self.insertions.append((anchor, action))

    def addSeparator(self):
        self.separator_count += 1

    def addAction(self, action):
        self._actions.append(action)


class FakeForm:
    def __init__(self, menu):
        self.menuTools = menu


class FakeMw:
    def __init__(self, menu):
        self.form = FakeForm(menu)


class UITests(unittest.TestCase):
    def test_resolve_interval_for_save_preserves_existing_when_disabled(self):
        value = ui._resolve_interval_for_save(
            check_on_startup_enabled=False,
            selected_value=ui.CUSTOM_INTERVAL_SENTINEL,
            custom_text="",
            existing_interval="7d",
        )
        self.assertEqual(value, "7d")

    def test_resolve_interval_for_save_falls_back_to_startup_when_disabled_and_invalid(self):
        value = ui._resolve_interval_for_save(
            check_on_startup_enabled=False,
            selected_value=ui.CUSTOM_INTERVAL_SENTINEL,
            custom_text="",
            existing_interval="not-valid",
        )
        self.assertEqual(value, "startup")

    def test_resolve_interval_for_save_validates_custom_when_enabled(self):
        value = ui._resolve_interval_for_save(
            check_on_startup_enabled=True,
            selected_value=ui.CUSTOM_INTERVAL_SENTINEL,
            custom_text="5h",
            existing_interval="startup",
        )
        self.assertEqual(value, "5h")

    def test_interval_presets_match_requested_options(self):
        self.assertEqual(
            ui.INTERVAL_PRESETS,
            (
                ("Startup", "startup"),
                ("Every day", "1d"),
                ("Every 7 days", "7d"),
                ("Every 30 days", "30d"),
                ("Custom...", ui.CUSTOM_INTERVAL_SENTINEL),
            ),
        )

    def test_add_menu_action_skips_duplicate(self):
        existing = FakeAction(name=ui.MENU_ACTION_OBJECT_NAME)
        menu = FakeMenu([existing])
        mw = FakeMw(menu)

        ui.add_menu_action(
            mw,
            callback=lambda: None,
            config_callback=lambda: None,
            action_factory=FakeAction,
            menu_factory=FakeSubMenu,
        )
        self.assertEqual(len(menu.actions()), 1)

    def test_add_menu_action_inserts_above_anchor(self):
        anchor = FakeAction(text="Upgrade/Downgrade", name="action_upgrade_downgrade")
        other = FakeAction(text="Preferences")
        menu = FakeMenu([other, anchor])
        mw = FakeMw(menu)

        ui.add_menu_action(
            mw,
            callback=lambda: None,
            config_callback=lambda: None,
            action_factory=FakeAction,
            menu_factory=FakeSubMenu,
        )
        actions = menu.actions()
        self.assertEqual(actions[1].objectName(), ui.MENU_ACTION_OBJECT_NAME)
        self.assertEqual(actions[1].text(), ui.MENU_ACTION_TEXT)
        submenu_actions = actions[1].menu().actions()
        self.assertEqual(len(submenu_actions), 2)
        self.assertEqual(submenu_actions[0].text(), ui.MENU_CHECK_ACTION_TEXT)
        self.assertEqual(submenu_actions[1].text(), ui.MENU_CONFIG_ACTION_TEXT)
        self.assertEqual(actions[2], anchor)

    def test_open_download_page_fallback_message(self):
        messages = []

        ui.open_download_page(
            "https://apps.ankiweb.net/",
            open_url_func=lambda _url: False,
            show_info_func=lambda message: messages.append(message),
        )

        self.assertEqual(len(messages), 1)
        self.assertIn("Open this URL in your browser", messages[0])

    def test_ask_user_parents_dialog_to_main_window(self):
        calls = {}

        aqt_mod = types.ModuleType("aqt")
        fake_mw = object()
        aqt_mod.mw = fake_mw

        utils_mod = types.ModuleType("aqt.utils")

        def fake_ask_user(message, parent=None):
            calls["message"] = message
            calls["parent"] = parent
            return True

        utils_mod.askUser = fake_ask_user

        old_aqt = sys.modules.get("aqt")
        old_utils = sys.modules.get("aqt.utils")
        sys.modules["aqt"] = aqt_mod
        sys.modules["aqt.utils"] = utils_mod
        try:
            self.assertTrue(ui.ask_user("hello"))
        finally:
            if old_aqt is None:
                sys.modules.pop("aqt", None)
            else:
                sys.modules["aqt"] = old_aqt
            if old_utils is None:
                sys.modules.pop("aqt.utils", None)
            else:
                sys.modules["aqt.utils"] = old_utils

        self.assertEqual(calls["message"], "hello")
        self.assertIs(calls["parent"], fake_mw)

    def test_show_info_parents_dialog_to_main_window(self):
        calls = {}

        aqt_mod = types.ModuleType("aqt")
        fake_mw = object()
        aqt_mod.mw = fake_mw

        utils_mod = types.ModuleType("aqt.utils")

        def fake_show_info(message, parent=None):
            calls["message"] = message
            calls["parent"] = parent

        utils_mod.showInfo = fake_show_info

        old_aqt = sys.modules.get("aqt")
        old_utils = sys.modules.get("aqt.utils")
        sys.modules["aqt"] = aqt_mod
        sys.modules["aqt.utils"] = utils_mod
        try:
            ui.show_info("notice")
        finally:
            if old_aqt is None:
                sys.modules.pop("aqt", None)
            else:
                sys.modules["aqt"] = old_aqt
            if old_utils is None:
                sys.modules.pop("aqt.utils", None)
            else:
                sys.modules["aqt.utils"] = old_utils

        self.assertEqual(calls["message"], "notice")
        self.assertIs(calls["parent"], fake_mw)


if __name__ == "__main__":
    unittest.main()
