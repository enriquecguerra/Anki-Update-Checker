import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()
from unittest.mock import patch

from update_checker_pkg import launcher_adapter


class FakeAction:
    def __init__(self, text="", name="", visible=True, enabled=True, submenu=None):
        self._text = text
        self._name = name
        self._visible = visible
        self._enabled = enabled
        self._submenu = submenu
        self.trigger_count = 0

    def objectName(self):
        return self._name

    def text(self):
        return self._text

    def isVisible(self):
        return self._visible

    def isEnabled(self):
        return self._enabled

    def trigger(self):
        self.trigger_count += 1

    def menu(self):
        return self._submenu


class FakeMenu:
    def __init__(self, actions=None):
        self._actions = list(actions or [])

    def actions(self):
        return list(self._actions)


class FakeForm:
    def __init__(self, tools_actions=None, menubar_actions=None):
        self.menuTools = FakeMenu(tools_actions)
        self.menubar = FakeMenu(menubar_actions)


class FakeMw:
    def __init__(self, tools_actions=None, menubar_actions=None):
        self.form = FakeForm(tools_actions=tools_actions, menubar_actions=menubar_actions)


class LauncherAdapterTests(unittest.TestCase):
    def test_native_available_false_when_no_launcher_prereq(self):
        mw = FakeMw()
        mw.on_upgrade_downgrade = lambda: None

        with patch("update_checker_pkg.launcher_adapter.launcher_executable_available", return_value=False):
            self.assertFalse(launcher_adapter.native_launcher_available(mw))

    def test_native_available_true_with_direct_handler_and_launcher(self):
        mw = FakeMw()
        mw.on_upgrade_downgrade = lambda: None

        with patch("update_checker_pkg.launcher_adapter.launcher_executable_available", return_value=True):
            self.assertTrue(launcher_adapter.native_launcher_available(mw))

    def test_try_run_native_launcher_calls_direct_handler(self):
        state = {"called": 0}
        mw = FakeMw()

        def _handler():
            state["called"] += 1

        mw.on_upgrade_downgrade = _handler

        with patch("update_checker_pkg.launcher_adapter.launcher_executable_available", return_value=True):
            self.assertTrue(launcher_adapter.try_run_native_launcher(mw))

        self.assertEqual(state["called"], 1)

    def test_try_run_native_launcher_falls_back_to_menu_action(self):
        action = FakeAction(text="Upgrade/Downgrade", name="action_upgrade_downgrade")
        mw = FakeMw(tools_actions=[action])

        with patch("update_checker_pkg.launcher_adapter.launcher_executable_available", return_value=False):
            self.assertTrue(launcher_adapter.try_run_native_launcher(mw))

        self.assertEqual(action.trigger_count, 1)

    def test_action_classifier_requires_both_tokens(self):
        action_ok = FakeAction(text="Upgrade/Downgrade")
        action_bad = FakeAction(text="Upgrade")
        self.assertTrue(launcher_adapter.is_upgrade_downgrade_action(action_ok))
        self.assertFalse(launcher_adapter.is_upgrade_downgrade_action(action_bad))


if __name__ == "__main__":
    unittest.main()
