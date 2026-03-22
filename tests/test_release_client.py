import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()

from update_checker_pkg.models import ReleaseInfo
from update_checker_pkg.release_client import GITHUB_LATEST_API, GITHUB_RELEASES_API, GitHubReleaseClient


class StubReleaseClient(GitHubReleaseClient):
    def __init__(self, responses):
        super().__init__()
        self._responses = responses

    def _http_get_json(self, url, timeout=10):
        queue = self._responses.get(url, [])
        if not queue:
            return None, "no response configured"
        return queue.pop(0)


class ReleaseClientTests(unittest.TestCase):
    def test_select_release_filters_drafts_and_prereleases(self):
        releases = [
            {"tag_name": "v25.10.0-beta", "draft": False, "prerelease": True},
            {"tag_name": "v25.09.2", "draft": False, "prerelease": False},
        ]
        selected = GitHubReleaseClient.select_release_from_list(releases)
        self.assertEqual(selected, ReleaseInfo(tag="25.09.2"))

    def test_select_release_ignores_prerelease_only_list(self):
        releases = [{"tag_name": "v25.10.0-beta", "draft": False, "prerelease": True}]
        selected = GitHubReleaseClient.select_release_from_list(releases)
        self.assertIsNone(selected)

    def test_fallback_to_latest_endpoint(self):
        client = StubReleaseClient(
            {
                GITHUB_RELEASES_API: [([{"draft": True, "prerelease": False, "tag_name": ""}], None)],
                GITHUB_LATEST_API: [({"tag_name": "v25.09.2", "prerelease": False}, None)],
            }
        )
        release, error = client.latest_release()
        self.assertIsNone(error)
        self.assertEqual(release, ReleaseInfo(tag="25.09.2"))

    def test_surfaces_error_when_no_valid_payload(self):
        client = StubReleaseClient(
            {
                GITHUB_RELEASES_API: [(None, "rate-limit")],
                GITHUB_LATEST_API: [(None, "network")],
            }
        )
        release, error = client.latest_release()
        self.assertIsNone(release)
        self.assertIn("Could not fetch latest version information", error)


if __name__ == "__main__":
    unittest.main()
