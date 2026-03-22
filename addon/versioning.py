# -*- coding: utf-8 -*-
"""Version normalization and comparison helpers."""

import re
from typing import Tuple


def extract_numeric_tokens(value: str) -> Tuple[int, ...]:
    """Extract numeric tokens from a version string.

    Examples:
      "25.09.1" -> (25, 9, 1)
      "v25.09" -> (25, 9)
      "25.09rc1" -> (25, 9, 1)
    """
    tokens = [int(item) for item in re.findall(r"\d+", str(value))]
    if not tokens:
        return (0,)
    return tuple(tokens)


def compare_versions(left: str, right: str) -> int:
    """Compare two version strings.

    Returns:
      1  if left > right
      0  if equal
      -1 if left < right
    """
    left_tokens = extract_numeric_tokens(left)
    right_tokens = extract_numeric_tokens(right)

    max_len = max(len(left_tokens), len(right_tokens))
    left_norm = left_tokens + (0,) * (max_len - len(left_tokens))
    right_norm = right_tokens + (0,) * (max_len - len(right_tokens))

    if left_norm > right_norm:
        return 1
    if left_norm < right_norm:
        return -1
    return 0


def is_newer(latest: str, current: str) -> bool:
    """Return True if latest version is newer than current."""
    return compare_versions(latest, current) > 0
