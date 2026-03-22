# -*- coding: utf-8 -*-
"""Update-check controller orchestrating config, network, and UI decisions."""

import time
from typing import Any, Callable, Optional

from . import config_state
from .intervals import should_run_now
from .launcher_adapter import current_anki_version_str, native_launcher_available, try_run_native_launcher
from .models import (
    CheckResult,
    STATUS_ERROR,
    STATUS_UP_TO_DATE,
    STATUS_UPDATE_AVAILABLE,
)
from .release_client import GitHubReleaseClient
from .ui import ask_user, open_configuration_dialog, open_download_page, show_info
from .versioning import is_newer


class UpdateCheckController:
    """Controller for automatic and manual update checks."""

    def __init__(
        self,
        module_name: str,
        mw: Any,
        release_client: Optional[GitHubReleaseClient] = None,
        now_provider: Optional[Callable[[], int]] = None,
        current_version_getter: Optional[Callable[[], str]] = None,
        launcher_available_func: Optional[Callable[[], bool]] = None,
        launcher_run_func: Optional[Callable[[], bool]] = None,
        ask_user_func: Optional[Callable[[str], bool]] = None,
        show_info_func: Optional[Callable[[str], None]] = None,
        open_download_page_func: Optional[Callable[[str], None]] = None,
        open_configuration_dialog_func: Optional[Callable[[Any], Optional[Any]]] = None,
    ):
        self.module_name = module_name
        self.mw = mw
        self.release_client = release_client or GitHubReleaseClient()

        self.now_provider = now_provider or (lambda: int(time.time()))
        self.current_version_getter = current_version_getter or (lambda: current_anki_version_str(self.mw))
        self.launcher_available_func = launcher_available_func or (lambda: native_launcher_available(self.mw))
        self.launcher_run_func = launcher_run_func or (lambda: try_run_native_launcher(self.mw))

        self.ask_user_func = ask_user_func or ask_user
        self.show_info_func = show_info_func or show_info
        self.open_download_page_func = open_download_page_func or open_download_page
        self.open_configuration_dialog_func = open_configuration_dialog_func or open_configuration_dialog

    def _load_raw_config(self):
        return config_state.load_raw_config(self.mw.addonManager, self.module_name)

    def _save_raw_config(self, raw):
        config_state.save_raw_config(self.mw.addonManager, self.module_name, raw)

    def run_manual_check(self) -> None:
        self._run_check_in_background(manual=True)

    def maybe_check_on_startup(self) -> None:
        raw = self._load_raw_config()
        normalized = config_state.normalize_config(raw)

        if not normalized.check_on_startup:
            return

        now_ts = int(self.now_provider())
        if not should_run_now(normalized.last_check_ts, now_ts, normalized.interval_seconds):
            return

        self._run_check_in_background(manual=False)

    def open_configuration(self) -> None:
        raw = self._load_raw_config()
        updated = self.open_configuration_dialog_func(raw)
        if updated is None:
            return
        self._save_raw_config(updated)

    def _run_check_in_background(self, manual: bool) -> None:
        def worker() -> CheckResult:
            raw = self._load_raw_config()
            normalized = config_state.normalize_config(raw)

            current = str(self.current_version_getter())
            latest_release, error = self.release_client.latest_release()
            if error or latest_release is None:
                return CheckResult(
                    status=STATUS_ERROR,
                    current=current,
                    error=error or "Could not fetch latest version information.",
                    download_url=normalized.download_page_url,
                )

            now_ts = int(self.now_provider())
            updated_raw = config_state.update_success_state(raw, now_ts, latest_release.tag)
            self._save_raw_config(updated_raw)

            if is_newer(latest_release.tag, current):
                native_available = bool(self.launcher_available_func())

                return CheckResult(
                    status=STATUS_UPDATE_AVAILABLE,
                    current=current,
                    latest=latest_release.tag,
                    download_url=normalized.download_page_url,
                    native_launcher_available=native_available,
                )

            return CheckResult(
                status=STATUS_UP_TO_DATE,
                current=current,
                latest=latest_release.tag,
                download_url=normalized.download_page_url,
            )

        def on_done(future):
            try:
                result = future.result() if hasattr(future, "result") else future
            except Exception as err:
                result = CheckResult(
                    status=STATUS_ERROR,
                    error="Background task failed: %s" % err,
                )
            self._finish_check(manual, result)

        self.mw.taskman.run_in_background(worker, on_done)

    def _finish_check(self, manual: bool, result: CheckResult) -> None:
        if result.status == STATUS_ERROR:
            if manual:
                self.show_info_func(
                    "Update check failed:\n%s\n\nOfficial download page:\n%s"
                    % (result.error or "Unknown error.", result.download_url)
                )
            return

        if result.status == STATUS_UP_TO_DATE:
            if manual:
                self.show_info_func(
                    "You are up to date.\n\nInstalled: %s\nLatest:    %s"
                    % (result.current or "?", result.latest or "?")
                )
            return

        if result.status != STATUS_UPDATE_AVAILABLE:
            if manual:
                self.show_info_func("Unexpected update-check state: %s" % result.status)
            return

        if result.native_launcher_available:
            if self.ask_user_func(
                "A new Anki version is available.\n\n"
                "Installed: %s\nLatest:    %s\n\n"
                "Run Anki's built-in Upgrade/Downgrade now?"
                % (result.current or "?", result.latest or "?")
            ):
                if not self.launcher_run_func():
                    if self.ask_user_func(
                        "Could not invoke the native upgrader.\n\n"
                        "Open the official download page instead?"
                    ):
                        self.open_download_page_func(result.download_url)
            else:
                if self.ask_user_func("Open the official download page instead?"):
                    self.open_download_page_func(result.download_url)
            return

        if self.ask_user_func(
            "A new Anki version is available.\n\n"
            "Installed: %s\nLatest:    %s\n\n"
            "Open the official download page now?"
            % (result.current or "?", result.latest or "?")
        ):
            self.open_download_page_func(result.download_url)
