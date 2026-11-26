"""Release checks with a simulated GitHub reply."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication
from pet.updates import UpdateChecker, parse_latest_release
from pet.version import VERSION


APP = QApplication.instance() or QApplication([])


class UpdateCheckerTests(unittest.TestCase):
    def test_compares_numeric_versions_and_builds_trusted_release_link(self):
        payload = {
            "tag_name": "v0.1.10",
            "html_url": "https://example.invalid/elsewhere",
            "draft": False,
            "prerelease": False,
        }
        release = parse_latest_release(payload, "0.1.9")
        self.assertEqual(release.version, "0.1.10")
        self.assertTrue(release.is_newer)
        self.assertEqual(
            release.url,
            "https://github.com/Jacky-zhengH/Fmm_DesktopPet/releases/tag/v0.1.10",
        )
        for current_version in ("0.1.10", "0.2.0"):
            with self.subTest(current_version=current_version):
                release = parse_latest_release(payload, current_version)
                self.assertEqual(release.version, "0.1.10")
                self.assertFalse(release.is_newer)
        for invalid_fields in ({"draft": True}, {"prerelease": True}, {"tag_name": "v0.1.10-beta"}):
            with self.subTest(invalid_fields=invalid_fields), self.assertRaises(ValueError):
                parse_latest_release(payload | invalid_fields, "0.1.9")

    def test_one_request_at_a_time_and_failed_refresh_keeps_last_success(self):
        checker = UpdateChecker(Path('settings.json'))
        self.addCleanup(checker.shutdown)
        major, minor, patch_number = map(int, VERSION.split("."))
        next_version = f"{major}.{minor}.{patch_number + 1}"
        response = Mock()
        response.error.return_value = QNetworkReply.NetworkError.NoError
        response.readAll.return_value = json.dumps({
            "tag_name": f"v{next_version}", "draft": False, "prerelease": False,
        }).encode("utf-8")
        failure = Mock()
        failure.error.return_value = QNetworkReply.NetworkError.TimeoutError
        network = Mock()
        network.get.side_effect = [response, failure]

        with patch.object(checker, "_network", network):
            self.assertFalse(checker._automatic_timer.isActive())
            checker.set_automatic(True)
            self.assertTrue(checker._automatic_timer.isActive())
            checker._automatic_timer.timeout.emit()
            checker.check()
            self.assertEqual(checker.state, "checking")
            network.get.assert_called_once()
            request = network.get.call_args.args[0]
            self.assertEqual(
                request.url().toString(),
                "https://api.github.com/repos/Jacky-zhengH/Fmm_DesktopPet/releases/latest",
            )
            self.assertFalse(request.hasRawHeader("Authorization"))

            response.finished.connect.call_args.args[0]()
            self.assertEqual(checker.state, "available")
            previous_success = checker.checked_at
            self.assertIsNotNone(previous_success)
            previous_release = checker.release
            self.assertEqual(previous_release.version, next_version)

            checker.check()
            failure.finished.connect.call_args.args[0]()
            self.assertEqual(checker.state, "failed")
            self.assertEqual(checker.checked_at, previous_success)
            self.assertEqual(checker.release, previous_release)
            checker.set_automatic(False)
            self.assertFalse(checker._automatic_timer.isActive())
