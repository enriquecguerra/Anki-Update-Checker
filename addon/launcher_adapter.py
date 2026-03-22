# -*- coding: utf-8 -*-
"""Anki launcher integration and version detection helpers."""

import unicodedata
from typing import Any, Iterable


def current_anki_version_str(mw: Any) -> str:
    """Best-effort version lookup in compatibility order."""
    try:
        from anki import buildinfo  # type: ignore

        value = getattr(buildinfo, "version", None)
        if value:
            return str(value)
    except Exception:
        pass

    try:
        from aqt import appVersion  # type: ignore

        if appVersion:
            return str(appVersion)
    except Exception:
        pass

    try:
        value = getattr(mw, "appVersion", None)
        if value:
            return str(value)
    except Exception:
        pass

    try:
        import anki as anki_pkg  # type: ignore

        value = getattr(anki_pkg, "__version__", None)
        if value:
            return str(value)
    except Exception:
        pass

    return "0.0.0"


def clean_label(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("&", "")
    try:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
    except Exception:
        pass
    return text.lower().strip()


def is_upgrade_downgrade_action(action: Any) -> bool:
    try:
        name = clean_label(action.objectName())
    except Exception:
        name = ""
    try:
        text = clean_label(action.text())
    except Exception:
        text = ""
    combined = "%s %s" % (name, text)
    return "upgrade" in combined and "downgrade" in combined


def _iter_action_tree(menu_like: Any) -> Iterable[Any]:
    actions = []
    try:
        actions = list(menu_like.actions())
    except Exception:
        return

    for action in actions:
        yield action
        try:
            submenu = action.menu()
        except Exception:
            submenu = None
        if submenu:
            for nested in _iter_action_tree(submenu):
                yield nested


def _action_is_triggerable(action: Any) -> bool:
    try:
        if hasattr(action, "isVisible") and not action.isVisible():
            return False
    except Exception:
        return False

    try:
        if hasattr(action, "isEnabled") and not action.isEnabled():
            return False
    except Exception:
        return False

    return True


def launcher_executable_available() -> bool:
    try:
        from aqt.package import launcher_executable  # type: ignore

        return bool(launcher_executable())
    except Exception:
        return False


def _callable_upgrade_handler(mw: Any):
    for attr in ("on_upgrade_downgrade", "onUpgradeDowngrade"):
        fn = getattr(mw, attr, None)
        if callable(fn):
            return fn
    return None


def native_launcher_available(mw: Any) -> bool:
    """Return true only when launcher prerequisites are present."""
    fn = _callable_upgrade_handler(mw)
    if fn and launcher_executable_available():
        return True

    try:
        tools_menu = getattr(mw.form, "menuTools", None)
        if tools_menu:
            for action in tools_menu.actions():
                if is_upgrade_downgrade_action(action) and _action_is_triggerable(action):
                    return True
    except Exception:
        pass

    try:
        menubar = getattr(mw.form, "menubar", None)
        if menubar:
            for action in _iter_action_tree(menubar):
                if is_upgrade_downgrade_action(action) and _action_is_triggerable(action):
                    return True
    except Exception:
        pass

    return False


def try_run_native_launcher(mw: Any) -> bool:
    """Attempt native launcher invocation via direct callable or menu action."""
    fn = _callable_upgrade_handler(mw)
    if fn and launcher_executable_available():
        try:
            fn()
            return True
        except Exception:
            pass

    try:
        tools_menu = getattr(mw.form, "menuTools", None)
        if tools_menu:
            for action in tools_menu.actions():
                if is_upgrade_downgrade_action(action) and _action_is_triggerable(action):
                    action.trigger()
                    return True
    except Exception:
        pass

    try:
        menubar = getattr(mw.form, "menubar", None)
        if menubar:
            for action in _iter_action_tree(menubar):
                if is_upgrade_downgrade_action(action) and _action_is_triggerable(action):
                    action.trigger()
                    return True
    except Exception:
        pass

    return False
