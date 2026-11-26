"""Check the public GitHub release channel without blocking the desktop pet."""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from pet.version import VERSION

_REPOSITORY = "Jacky-zhengH/Fmm_DesktopPet"
_LATEST_RELEASE_URL = f"https://api.github.com/repos/{_REPOSITORY}/releases/latest"
_RELEASE_TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_INITIAL_DELAY_MS = 5000
_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000
_TIMEOUT_MS = 8000
_NOTES_LIMIT = 120


@dataclass(frozen=True)
class Release:
    version: str
    url: str
    notes: str
    is_newer: bool


def parse_latest_release(payload, current_version=VERSION) -> Release:
    if (not isinstance(payload, dict) or payload.get("draft") is not False
            or payload.get("prerelease") is not False):
        raise ValueError("Expected a published stable release")
    tag = payload.get("tag_name")
    version = _RELEASE_TAG.fullmatch(tag) if isinstance(tag, str) else None
    if version is None:
        raise ValueError("Invalid stable release tag")
    is_newer = tuple(map(int, version.groups())) > tuple(map(int, current_version.split(".")))

    body = payload.get("body")
    notes = ""
    if isinstance(body, str):
        notes = next((line for line in map(str.strip, body.splitlines())
                      if line and not line.startswith("#")), "")
    if len(notes) > _NOTES_LIMIT:
        notes = notes[:_NOTES_LIMIT - 1] + "…"
    return Release(tag[1:], f"https://github.com/{_REPOSITORY}/releases/tag/{tag}", notes, is_newer)


class UpdateChecker(QObject):
    changed = Signal()

    def __init__(self, settings_path, automatic=False, parent=None):
        super().__init__(parent)
        self.state = "idle"
        self.release = None
        self.checked_at = None
        self._closed = False
        self._reply = None
        self._network = QNetworkAccessManager(self)
        self._allow_automatic = settings_path is not None
        self._automatic = False
        self._automatic_timer = QTimer(self)
        self._automatic_timer.setSingleShot(True)
        self._automatic_timer.timeout.connect(self.check)
        self.set_automatic(automatic)

    def set_automatic(self, enabled):
        enabled = bool(enabled and self._allow_automatic and not self._closed)
        if enabled == self._automatic:
            return
        self._automatic = enabled
        if enabled:
            self._automatic_timer.start(_INITIAL_DELAY_MS)
        else:
            self._automatic_timer.stop()

    def check(self):
        if self._closed:
            return
        if self._automatic:
            self._automatic_timer.start(_CHECK_INTERVAL_MS)
        if self._reply is not None:
            return

        request = QNetworkRequest(QUrl(_LATEST_RELEASE_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"X-GitHub-Api-Version", b"2026-03-10")
        request.setRawHeader(b"User-Agent", f"Fmm-DesktopPet/{VERSION}".encode("ascii"))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.SameOriginRedirectPolicy)
        request.setTransferTimeout(_TIMEOUT_MS)
        self._reply = self._network.get(request)
        self._reply.finished.connect(self._finish_check)
        self.state = "checking"
        self.changed.emit()

    def _finish_check(self):
        reply, self._reply = self._reply, None
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError("GitHub request failed")
            self.release = parse_latest_release(json.loads(bytes(reply.readAll())))
        except ValueError:
            self.state = "failed"
        else:
            self.checked_at = datetime.now(timezone.utc)
            self.state = "available" if self.release.is_newer else "current"
        finally:
            reply.deleteLater()
        self.changed.emit()

    def shutdown(self):
        self._closed = True
        self.set_automatic(False)
        reply, self._reply = self._reply, None
        if reply is not None:
            reply.abort()
            reply.deleteLater()
