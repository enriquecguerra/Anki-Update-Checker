import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()

from update_checker_pkg.controller import UpdateCheckController
from update_checker_pkg.models import ReleaseInfo


class FakeAddonManager:
    def __init__(self, config):
        self._config = dict(config)
        self.writes = []

    def getConfig(self, module_name):
        return dict(self._config)

    def writeConfig(self, module_name, config):
        self._config = dict(config)
        self.writes.append(dict(config))


class CompletedFuture:
    def __init__(self, value=None, error=None):
        self._value = value
        self._error = error

    def result(self):
        if self._error is not None:
            raise self._error
        return self._value


class ImmediateTaskMan:
    def run_in_background(self, worker, on_done):
        try:
            value = worker()
            fut = CompletedFuture(value=value)
        except Exception as err:
            fut = CompletedFuture(error=err)
        on_done(fut)


class FakeMw:
    def __init__(self, config):
        self.addonManager = FakeAddonManager(config)
        self.taskman = ImmediateTaskMan()


class StubReleaseClient:
    def __init__(self, release=None, error=None):
        self.release = release
        self.error = error

    def latest_release(self):
        return self.release, self.error


class ControllerTests(unittest.TestCase):
    def _base_config(self):
        return {
            "check_on_startup": True,
            "check_interval": "startup",
            "download_page_url": "https://apps.ankiweb.net/",
            "_last_check_ts": 0,
            "_last_known_latest": "",
        }

    def test_startup_error_is_silent(self):
        messages = []
        mw = FakeMw(self._base_config())
        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=None, error="network"),
            show_info_func=lambda message: messages.append(message),
            ask_user_func=lambda _message: False,
            current_version_getter=lambda: "25.07.5",
        )

        controller.maybe_check_on_startup()
        self.assertEqual(messages, [])
        self.assertEqual(mw.addonManager.writes, [])

    def test_manual_error_is_visible(self):
        messages = []
        mw = FakeMw(self._base_config())
        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=None, error="network"),
            show_info_func=lambda message: messages.append(message),
            ask_user_func=lambda _message: False,
            current_version_getter=lambda: "25.07.5",
        )

        controller.run_manual_check()
        self.assertEqual(len(messages), 1)
        self.assertIn("Update check failed", messages[0])
        self.assertEqual(mw.addonManager.writes, [])

    def test_success_updates_internal_state(self):
        prompts = []
        mw = FakeMw(self._base_config())
        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=ReleaseInfo(tag="25.09.2")),
            show_info_func=lambda _message: None,
            ask_user_func=lambda message: prompts.append(message) or False,
            current_version_getter=lambda: "25.07.5",
            now_provider=lambda: 111,
            launcher_available_func=lambda: False,
        )

        controller.run_manual_check()

        self.assertEqual(len(mw.addonManager.writes), 1)
        written = mw.addonManager.writes[0]
        self.assertEqual(written["_last_check_ts"], 111)
        self.assertEqual(written["_last_known_latest"], "25.09.2")
        self.assertEqual(len(prompts), 1)

    def test_success_write_strips_removed_legacy_key(self):
        prompts = []
        cfg = self._base_config()
        cfg["check_interval_days"] = 3
        mw = FakeMw(cfg)
        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=ReleaseInfo(tag="25.09.2")),
            show_info_func=lambda _message: None,
            ask_user_func=lambda message: prompts.append(message) or False,
            current_version_getter=lambda: "25.07.5",
            now_provider=lambda: 111,
            launcher_available_func=lambda: False,
        )

        controller.run_manual_check()

        self.assertEqual(len(mw.addonManager.writes), 1)
        written = mw.addonManager.writes[0]
        self.assertNotIn("check_interval_days", written)

    def test_update_path_probes_native_launcher(self):
        calls = {"launcher_available": 0}
        prompts = []
        mw = FakeMw(self._base_config())

        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=ReleaseInfo(tag="25.10.0")),
            show_info_func=lambda _message: None,
            ask_user_func=lambda message: prompts.append(message) or False,
            current_version_getter=lambda: "25.09.2",
            launcher_available_func=lambda: calls.__setitem__("launcher_available", calls["launcher_available"] + 1) or False,
            now_provider=lambda: 222,
        )

        controller.run_manual_check()

        self.assertEqual(calls["launcher_available"], 1)
        self.assertEqual(len(prompts), 1)
        self.assertIn("new anki version is available", prompts[0].lower())

    def test_manual_up_to_date_message(self):
        messages = []
        mw = FakeMw(self._base_config())
        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=ReleaseInfo(tag="25.09.2")),
            show_info_func=lambda message: messages.append(message),
            ask_user_func=lambda _message: False,
            current_version_getter=lambda: "25.09.2",
            now_provider=lambda: 333,
        )

        controller.run_manual_check()

        self.assertEqual(len(messages), 1)
        self.assertIn("You are up to date", messages[0])

    def test_open_configuration_writes_returned_config(self):
        mw = FakeMw(self._base_config())
        saved = dict(self._base_config())
        saved["check_interval"] = "6h"

        controller = UpdateCheckController(
            module_name="unpacked",
            mw=mw,
            release_client=StubReleaseClient(release=None, error="unused"),
            open_configuration_dialog_func=lambda _raw: dict(saved),
            show_info_func=lambda _message: None,
            ask_user_func=lambda _message: False,
            current_version_getter=lambda: "25.09.2",
        )

        controller.open_configuration()

        self.assertEqual(len(mw.addonManager.writes), 1)
        self.assertEqual(mw.addonManager.writes[0]["check_interval"], "6h")


if __name__ == "__main__":
    unittest.main()
