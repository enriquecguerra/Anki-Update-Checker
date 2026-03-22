# -*- coding: utf-8 -*-
"""UI helpers for menus and dialogs."""

import re
from typing import Any, Callable, Dict, Iterable, Optional

from .config_state import DEFAULT_CONFIG
from .launcher_adapter import clean_label, is_upgrade_downgrade_action

MENU_ACTION_TEXT = "Update Checker"
MENU_ACTION_OBJECT_NAME = "updateCheckerMenu"
MENU_ACTION_TOOLTIP = "Check for updates and configure Update Checker"

MENU_CHECK_ACTION_TEXT = "Check for Updates"
MENU_CHECK_ACTION_OBJECT_NAME = "updateCheckerCheckAction"

MENU_CONFIG_ACTION_TEXT = "Change Configuration"
MENU_CONFIG_ACTION_OBJECT_NAME = "updateCheckerConfigAction"

CUSTOM_INTERVAL_SENTINEL = "__custom_interval__"
INTERVAL_PRESETS = (
    ("Startup", "startup"),
    ("Every day", "1d"),
    ("Every 7 days", "7d"),
    ("Every 30 days", "30d"),
    ("Custom...", CUSTOM_INTERVAL_SENTINEL),
)


def is_upgrade_or_downgrade_hint(action: Any) -> bool:
    try:
        name = clean_label(action.objectName())
    except Exception:
        name = ""
    try:
        text = clean_label(action.text())
    except Exception:
        text = ""
    combined = "%s %s" % (name, text)
    return ("upgrade" in combined and "downgrade" in combined) or ("upgrade" in combined) or (
        "downgrade" in combined
    )


def has_update_checker_action(actions: Iterable[Any]) -> bool:
    for action in actions:
        try:
            if (action.objectName() or "") == MENU_ACTION_OBJECT_NAME:
                return True
        except Exception:
            pass
        try:
            submenu = action.menu()
            if submenu and (submenu.objectName() or "") == MENU_ACTION_OBJECT_NAME:
                return True
        except Exception:
            pass
    return False


def find_insert_anchor(actions: Iterable[Any]) -> Optional[Any]:
    for action in actions:
        if is_upgrade_downgrade_action(action):
            return action
    for action in actions:
        if is_upgrade_or_downgrade_hint(action):
            return action
    return None


def open_download_page(
    url: str,
    open_url_func: Optional[Callable[[str], bool]] = None,
    show_info_func: Optional[Callable[[str], None]] = None,
) -> None:
    """Open URL in browser and fall back to copyable dialog on failure."""
    if open_url_func is None:
        from aqt.qt import QDesktopServices, QUrl

        def _default_open(target: str) -> bool:
            try:
                return bool(QDesktopServices.openUrl(QUrl(target)))
            except Exception:
                return False

        open_url_func = _default_open

    if show_info_func is None:
        from aqt import mw
        from aqt.utils import showInfo

        def _default_show_info(message: str) -> None:
            showInfo(message, parent=mw)

        show_info_func = _default_show_info

    ok = False
    try:
        ok = bool(open_url_func(url))
    except Exception:
        ok = False

    if not ok:
        show_info_func("Open this URL in your browser:\n%s" % url)


def add_menu_action(
    mw: Any,
    callback: Callable[[], None],
    config_callback: Callable[[], None],
    action_factory: Optional[Callable[[str, Any], Any]] = None,
    menu_factory: Optional[Callable[[str, Any], Any]] = None,
) -> None:
    """Add the Update Checker submenu once per session/profile."""
    menu = mw.form.menuTools
    actions = list(menu.actions())
    if has_update_checker_action(actions):
        return

    if action_factory is None:
        from aqt.qt import QAction

        action_factory = QAction

    if menu_factory is None:
        from aqt.qt import QMenu

        menu_factory = QMenu

    submenu = menu_factory(MENU_ACTION_TEXT, mw)
    submenu.setObjectName(MENU_ACTION_OBJECT_NAME)

    check_action = action_factory(MENU_CHECK_ACTION_TEXT, mw)
    check_action.setObjectName(MENU_CHECK_ACTION_OBJECT_NAME)
    check_action.triggered.connect(lambda _=False: callback())
    submenu.addAction(check_action)

    config_action = action_factory(MENU_CONFIG_ACTION_TEXT, mw)
    config_action.setObjectName(MENU_CONFIG_ACTION_OBJECT_NAME)
    config_action.triggered.connect(lambda _=False: config_callback())
    submenu.addAction(config_action)

    action = submenu.menuAction()
    action.setObjectName(MENU_ACTION_OBJECT_NAME)
    action.setToolTip(MENU_ACTION_TOOLTIP)

    anchor = find_insert_anchor(actions)
    if anchor is not None:
        menu.insertAction(anchor, action)
        return

    try:
        menu.addSeparator()
    except Exception:
        pass
    menu.addAction(action)


def ask_user(message: str) -> bool:
    from aqt import mw
    from aqt.utils import askUser

    return bool(askUser(message, parent=mw))


def show_info(message: str) -> None:
    from aqt import mw
    from aqt.utils import showInfo

    showInfo(message, parent=mw)


def _normalize_interval_input(value: str) -> Optional[Any]:
    lowered = str(value or "").strip().lower().replace(" ", "")
    if not lowered:
        return None
    if lowered in ("startup", "always", "eachstartup", "everystartup", "0", "0d", "0h", "0m", "0s"):
        return "startup"
    if lowered in ("never", "off", "disabled"):
        return "never"
    if re.match(r"^\d+[smhd]$", lowered):
        return lowered
    try:
        numeric = float(lowered)
    except Exception:
        return None
    if numeric < 0:
        return None
    if numeric.is_integer():
        return int(numeric)
    return numeric


def open_configuration_dialog(raw_config: Any) -> Optional[Dict[str, Any]]:
    from aqt import mw
    from aqt.qt import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QVBoxLayout,
        QWidget,
    )

    config = dict(raw_config) if isinstance(raw_config, dict) else {}
    for key, default in DEFAULT_CONFIG.items():
        config.setdefault(key, default)
    config.pop("check_interval_days", None)

    dialog = QDialog(mw)
    dialog.setWindowTitle("Update Checker Configuration")
    dialog.setObjectName("updateCheckerConfigDialog")
    dialog.setMinimumWidth(560)

    root_layout = QVBoxLayout(dialog)
    description = QLabel("Set how often Update Checker runs automatically and where to open downloads.")
    description.setWordWrap(True)
    root_layout.addWidget(description)

    form = QFormLayout()
    root_layout.addLayout(form)

    check_on_startup = QCheckBox("Enable automatic checks on profile open")
    check_on_startup.setChecked(bool(config.get("check_on_startup", True)))
    form.addRow("Automatic checks", check_on_startup)

    interval_wrapper = QWidget(dialog)
    interval_layout = QVBoxLayout(interval_wrapper)
    interval_layout.setContentsMargins(0, 0, 0, 0)

    interval_combo = QComboBox(dialog)
    for label, value in INTERVAL_PRESETS:
        interval_combo.addItem(label, value)
    interval_layout.addWidget(interval_combo)

    custom_interval = QLineEdit(dialog)
    custom_interval.setPlaceholderText("Custom interval (e.g., 5m, 5h, 5d, etc.)")
    custom_interval.setMinimumHeight(max(32, custom_interval.sizeHint().height() + 8))
    interval_layout.addWidget(custom_interval)
    form.addRow("Check interval", interval_wrapper)

    download_page_url = QLineEdit(dialog)
    download_page_url.setText(str(config.get("download_page_url") or DEFAULT_CONFIG["download_page_url"]))
    form.addRow("Download page URL", download_page_url)

    error_label = QLabel("")
    error_label.setWordWrap(True)
    error_label.setStyleSheet("color: #b00020;")
    root_layout.addWidget(error_label)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    root_layout.addWidget(buttons)

    interval_raw = config.get("check_interval", DEFAULT_CONFIG["check_interval"])
    if isinstance(interval_raw, (int, float)):
        normalized_interval = str(interval_raw)
    else:
        normalized_interval = str(interval_raw).strip() or str(DEFAULT_CONFIG["check_interval"])
    normalized_lowered = normalized_interval.lower().replace(" ", "")

    preset_index = -1
    for idx in range(interval_combo.count()):
        preset_value = str(interval_combo.itemData(idx))
        if preset_value == normalized_lowered:
            preset_index = idx
            break

    if preset_index >= 0:
        interval_combo.setCurrentIndex(preset_index)
        custom_interval.setText("")
    else:
        for idx in range(interval_combo.count()):
            if interval_combo.itemData(idx) == CUSTOM_INTERVAL_SENTINEL:
                interval_combo.setCurrentIndex(idx)
                break
        custom_interval.setText(normalized_interval)

    def sync_interval_state(*_args: Any) -> None:
        is_custom = interval_combo.currentData() == CUSTOM_INTERVAL_SENTINEL
        custom_interval.setEnabled(is_custom and check_on_startup.isChecked())
        custom_interval.setVisible(is_custom)
        interval_wrapper.setEnabled(check_on_startup.isChecked())
        if is_custom:
            dialog.adjustSize()
            size_hint = dialog.sizeHint()
            dialog.resize(max(dialog.width(), size_hint.width()), max(dialog.height(), size_hint.height()))

    interval_combo.currentIndexChanged.connect(sync_interval_state)
    check_on_startup.toggled.connect(sync_interval_state)
    sync_interval_state()
    dialog.resize(max(dialog.width(), 560), max(dialog.height(), 300))

    result: Dict[str, Any] = {}

    def on_accept() -> None:
        selected = interval_combo.currentData()
        interval_value = custom_interval.text() if selected == CUSTOM_INTERVAL_SENTINEL else str(selected)
        parsed_interval = _normalize_interval_input(interval_value)
        if parsed_interval is None:
            error_label.setText(
                "Invalid interval. Use startup, never, <N><s|m|h|d>, or a number interpreted as days."
            )
            return

        url = str(download_page_url.text() or "").strip()
        if not url:
            url = DEFAULT_CONFIG["download_page_url"]

        updated = dict(config)
        updated.pop("check_interval_days", None)
        updated["check_on_startup"] = bool(check_on_startup.isChecked())
        updated["check_interval"] = parsed_interval
        updated["download_page_url"] = url

        result["config"] = updated
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)

    if dialog.exec():
        return result.get("config")
    return None
