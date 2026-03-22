# -*- coding: utf-8 -*-
"""GitHub release lookup client for Anki releases."""

import json
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import ReleaseInfo

GITHUB_RELEASES_API = "https://api.github.com/repos/ankitects/anki/releases"
GITHUB_LATEST_API = "https://api.github.com/repos/ankitects/anki/releases/latest"
USER_AGENT = "anki-addon-update-checker/2.0 (https://apps.ankiweb.net/)"


class GitHubReleaseClient:
    """Fetch and select latest release info from GitHub."""

    def _http_get_json(self, url: str, timeout: int = 10) -> Tuple[Optional[Any], Optional[str]]:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        }
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = int(getattr(response, "status", 0) or 0)
                if status != 200:
                    if status == 403:
                        return None, "GitHub API rate limit or access denied."
                    return None, "HTTP %s" % status
                payload = response.read().decode("utf-8")
                return json.loads(payload), None
        except Exception as err:  # pragma: no cover - exercised through public API tests
            return None, str(err)

    @staticmethod
    def select_release_from_list(releases: Sequence[Dict[str, Any]]) -> Optional[ReleaseInfo]:
        """Select newest eligible release from API list payload."""
        for release in releases:
            if not isinstance(release, dict):
                continue
            if release.get("draft"):
                continue

            if bool(release.get("prerelease")):
                continue

            tag = str(release.get("tag_name") or "").lstrip("v").strip()
            if not tag:
                continue

            return ReleaseInfo(tag=tag)
        return None

    @staticmethod
    def release_from_latest_payload(payload: Dict[str, Any]) -> Optional[ReleaseInfo]:
        """Build ReleaseInfo from /releases/latest payload."""
        if not isinstance(payload, dict):
            return None
        if bool(payload.get("prerelease", False)):
            return None

        tag = str(payload.get("tag_name") or "").lstrip("v").strip()
        if not tag:
            return None

        return ReleaseInfo(tag=tag)

    def latest_release(self) -> Tuple[Optional[ReleaseInfo], Optional[str]]:
        """Return (release_info, error)."""
        list_payload, list_error = self._http_get_json(GITHUB_RELEASES_API)
        if isinstance(list_payload, list):
            release = self.select_release_from_list(list_payload)
            if release:
                return release, None

        latest_payload, latest_error = self._http_get_json(GITHUB_LATEST_API)
        if isinstance(latest_payload, dict):
            release = self.release_from_latest_payload(latest_payload)
            if release:
                return release, None

        errors: List[str] = []
        if list_error:
            errors.append("releases endpoint: %s" % list_error)
        if latest_error:
            errors.append("latest endpoint: %s" % latest_error)

        if errors:
            return None, "Could not fetch latest version information (%s)." % "; ".join(errors)
        return None, "Could not fetch latest version information."
