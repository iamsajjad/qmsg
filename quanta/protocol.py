"""Shared state and wire-format helpers for the two peer demo."""

from __future__ import annotations

from collections import OrderedDict, deque
import json
from threading import RLock
from typing import Any, Iterable


class PeerConnectionError(RuntimeError):
    """Raised when the other demo container cannot complete a request."""


def canonical_aad(session_id: str, sender: str, receiver: str) -> bytes:
    """Create stable authenticated metadata for an encrypted message."""
    value = {
        "protocol": "assignment2-e91-aes-v1",
        "receiver": receiver,
        "sender": sender,
        "session_id": session_id,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def receiver_candidate_bits(
    bob_settings: list[str],
    receiver_rows: Iterable[dict[str, Any]],
) -> str:
    """Sift and correct the receiver's anti-correlated singlet outcomes."""
    rows = list(receiver_rows)
    if len(bob_settings) != len(rows):
        raise ValueError("settings and outcome rows must contain the same number of rounds")

    bits: list[str] = []
    for setting, row in zip(bob_settings, rows, strict=True):
        alice_setting = row.get("alice_setting")
        bob_bit = row.get("bob_bit")
        if alice_setting not in {"K", "A0", "A1"}:
            raise ValueError("outcome row contains an unknown sender setting")
        if bob_bit not in {0, 1}:
            raise ValueError("outcome row contains an invalid receiver bit")
        if alice_setting == "K" and setting == "K":
            bits.append(str(1 - bob_bit))
    return "".join(bits)


class PeerState:
    """Thread-safe bounded storage for pending sessions and local messages."""

    def __init__(self, max_sessions: int = 32, max_messages: int = 100) -> None:
        self._max_sessions = max_sessions
        self._settings: OrderedDict[str, list[str]] = OrderedDict()
        self._sessions: OrderedDict[str, bytes] = OrderedDict()
        self._messages: deque[dict[str, Any]] = deque(maxlen=max_messages)
        self._lock = RLock()

    def store_settings(self, session_id: str, settings: list[str]) -> None:
        with self._lock:
            self._settings[session_id] = list(settings)
            self._settings.move_to_end(session_id)
            while len(self._settings) > self._max_sessions:
                self._settings.popitem(last=False)

    def consume_settings(self, session_id: str) -> list[str] | None:
        with self._lock:
            return self._settings.pop(session_id, None)

    def store_session(self, session_id: str, key: bytes) -> None:
        with self._lock:
            self._sessions[session_id] = key
            self._sessions.move_to_end(session_id)
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)

    def consume_session(self, session_id: str) -> bytes | None:
        with self._lock:
            return self._sessions.pop(session_id, None)

    def add_message(self, message: dict[str, Any]) -> None:
        with self._lock:
            self._messages.append(dict(message))

    def messages(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in reversed(self._messages)]
