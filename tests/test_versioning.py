import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()

from update_checker_pkg.versioning import compare_versions, extract_numeric_tokens, is_newer


class VersioningTests(unittest.TestCase):
    def test_extract_tokens(self):
        self.assertEqual(extract_numeric_tokens("v25.09.2"), (25, 9, 2))
        self.assertEqual(extract_numeric_tokens("25.09rc1"), (25, 9, 1))
        self.assertEqual(extract_numeric_tokens("no-version"), (0,))

    def test_compare_dynamic_padding(self):
        self.assertEqual(compare_versions("25.09", "25.09.0"), 0)
        self.assertEqual(compare_versions("25.10", "25.9.9"), 1)
        self.assertEqual(compare_versions("25.09.1", "25.09.2"), -1)

    def test_is_newer(self):
        self.assertTrue(is_newer("25.09.2", "25.07.5"))
        self.assertFalse(is_newer("25.07.5", "25.07.5"))


if __name__ == "__main__":
    unittest.main()
