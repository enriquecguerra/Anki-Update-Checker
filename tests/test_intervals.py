import unittest
from _test_loader import ensure_package_loaded
ensure_package_loaded()

from update_checker_pkg.intervals import interval_seconds_from_config, should_run_now


class IntervalTests(unittest.TestCase):
    def test_startup_aliases(self):
        self.assertEqual(interval_seconds_from_config({"check_interval": "startup"}), 0)
        self.assertEqual(interval_seconds_from_config({"check_interval": "0h"}), 0)

    def test_never_aliases(self):
        self.assertIsNone(interval_seconds_from_config({"check_interval": "never"}))
        self.assertIsNone(interval_seconds_from_config({"check_interval": "off"}))

    def test_unit_parsing(self):
        self.assertEqual(interval_seconds_from_config({"check_interval": "30m"}), 1800)
        self.assertEqual(interval_seconds_from_config({"check_interval": "2h"}), 7200)
        self.assertEqual(interval_seconds_from_config({"check_interval": "3d"}), 259200)

    def test_numeric_check_interval_is_days(self):
        self.assertEqual(interval_seconds_from_config({"check_interval": 2}), 172800)

    def test_removed_legacy_key_is_ignored(self):
        self.assertEqual(interval_seconds_from_config({"check_interval_days": 1.5}), 0)

    def test_invalid_interval_falls_back_to_startup(self):
        self.assertEqual(interval_seconds_from_config({"check_interval": "nonsense"}), 0)

    def test_should_run_now_logic(self):
        self.assertTrue(should_run_now(0, 100, 0))
        self.assertFalse(should_run_now(100, 150, 60))
        self.assertTrue(should_run_now(100, 161, 60))
        self.assertFalse(should_run_now(100, 1000, None))


if __name__ == "__main__":
    unittest.main()
