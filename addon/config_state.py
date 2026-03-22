# -*- coding: utf-8 -*-
"""Config loading, normalization, and state persistence."""

from typing import Any, Dict

from .intervals import interval_seconds_from_config
from .models import NormalizedConfig

DEFAULT_CONFIG = {
    "check_on_startup": True,
    "check_interval": "startup",
    "download_page_url": "https://apps.ankiweb.net/",
    "_last_check_ts": 0,
    "_last_known_latest": "",
}
DEPRECATED_KEYS = ("check_interval_days", "include_prereleases")


def _as_bool(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "on", "1"):
            return True
        if lowered in ("false", "no", "off", "0"):
            return False
    return fallback


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def load_raw_config(addon_manager: Any, module_name: str) -> Dict[str, Any]:
    raw = addon_manager.getConfig(module_name) or {}
    if not isinstance(raw, dict):
        raw = {}

    merged = dict(raw)
    for key in DEPRECATED_KEYS:
        merged.pop(key, None)
    for key, default in DEFAULT_CONFIG.items():
        merged.setdefault(key, default)
    return merged


def normalize_config(raw: Dict[str, Any]) -> NormalizedConfig:
    download_page_url = str(raw.get("download_page_url") or DEFAULT_CONFIG["download_page_url"]).strip()
    if not download_page_url:
        download_page_url = DEFAULT_CONFIG["download_page_url"]

    return NormalizedConfig(
        check_on_startup=_as_bool(raw.get("check_on_startup"), True),
        interval_seconds=interval_seconds_from_config(raw),
        download_page_url=download_page_url,
        last_check_ts=_as_int(raw.get("_last_check_ts", 0), 0),
    )


def save_raw_config(addon_manager: Any, module_name: str, raw: Dict[str, Any]) -> None:
    sanitized = dict(raw)
    for key in DEPRECATED_KEYS:
        sanitized.pop(key, None)
    addon_manager.writeConfig(module_name, sanitized)


def update_success_state(raw: Dict[str, Any], now_ts: int, latest_tag: str) -> Dict[str, Any]:
    updated = dict(raw)
    for key in DEPRECATED_KEYS:
        updated.pop(key, None)
    updated["_last_check_ts"] = int(now_ts)
    updated["_last_known_latest"] = str(latest_tag)
    return updated
