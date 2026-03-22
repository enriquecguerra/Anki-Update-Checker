# -*- coding: utf-8 -*-
"""Typed models used by the update checker."""

from dataclasses import dataclass
from typing import Optional

STATUS_UPDATE_AVAILABLE = "update_available"
STATUS_UP_TO_DATE = "up_to_date"
STATUS_ERROR = "error"


@dataclass
class NormalizedConfig:
    check_on_startup: bool
    interval_seconds: Optional[int]
    download_page_url: str
    last_check_ts: int


@dataclass
class ReleaseInfo:
    tag: str


@dataclass
class CheckResult:
    status: str
    current: Optional[str] = None
    latest: Optional[str] = None
    download_url: str = "https://apps.ankiweb.net/"
    native_launcher_available: bool = False
    error: Optional[str] = None
