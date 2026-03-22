# -*- coding: utf-8 -*-
"""Update Checker."""


def _register() -> None:
    from .bootstrap import register_hooks

    register_hooks()


try:
    _register()
except ModuleNotFoundError as err:
    # Allow imports in non-Anki environments (tests/docs tooling).
    if getattr(err, "name", "") != "aqt":
        raise
