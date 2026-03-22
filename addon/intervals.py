# -*- coding: utf-8 -*-
"""Interval parsing and scheduling utilities."""

import re
from typing import Any, Mapping, Optional


def interval_seconds_from_config(cfg: Mapping[str, Any]) -> Optional[int]:
    """Return interval in seconds.

    Returns:
      - int: check interval in seconds
      - 0: check every startup
      - None: disable automatic checks
    """
    val = cfg.get("check_interval", None)

    if isinstance(val, str):
        lowered = val.strip().lower()
        if lowered in ("startup", "always", "each startup", "every startup", "0", "0d", "0h", "0m", "0s"):
            return 0
        if lowered in ("never", "off", "disabled"):
            return None

        match = re.match(r"^(\d+)\s*([smhd])$", lowered)
        if match:
            count = int(match.group(1))
            unit = match.group(2)
            multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
            return count * multiplier

    if isinstance(val, (int, float)):
        try:
            return max(0, int(float(val) * 86400))
        except Exception:
            pass

    return 0


def should_run_now(last_check_ts: int, now_ts: int, interval_seconds: Optional[int]) -> bool:
    """Return whether a check should run now."""
    if interval_seconds is None:
        return False
    if interval_seconds <= 0:
        return True
    return (now_ts - int(last_check_ts)) >= interval_seconds
