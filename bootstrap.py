# -*- coding: utf-8 -*-
"""Anki hook bootstrap for the update checker add-on."""

from typing import Optional

from aqt import gui_hooks, mw

from .controller import UpdateCheckController
from .ui import add_menu_action

_CONTROLLER: Optional[UpdateCheckController] = None
_HOOK_REGISTERED = False


def _module_name() -> str:
    return __name__.split(".")[0]


def _controller() -> UpdateCheckController:
    global _CONTROLLER
    if _CONTROLLER is None:
        _CONTROLLER = UpdateCheckController(module_name=_module_name(), mw=mw)
    return _CONTROLLER


def on_profile_did_open() -> None:
    controller = _controller()
    add_menu_action(mw, controller.run_manual_check, controller.open_configuration)
    controller.maybe_check_on_startup()


def register_hooks() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.profile_did_open.append(on_profile_did_open)
    _HOOK_REGISTERED = True
