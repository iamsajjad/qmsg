"""Role-configured Flask application for Alice and Bob."""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
import os
import secrets
from typing import Any, Protocol
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from flask import Flask, jsonify, render_template, request
import requests

from quanta.crypto import EncryptedPayload, decrypt_message, derive_aes_key, encrypt_message
from quanta.e91 import generate_bob_settings, run_e91
from quanta.protocol import (
    PeerConnectionError,
    PeerState,
    canonical_aad,
    receiver_candidate_bits,
)


class PeerTransport(Protocol):
    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class RequestsPeerTransport:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers={"X-Peer-Token": self.token},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise PeerConnectionError(str(exc)) from exc


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _valid_session_id(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 100


def create_app(
    config: dict[str, Any] | None = None,
    transport: PeerTransport | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        ROLE=os.getenv("ROLE", "Alice"),
        PEER_NAME=os.getenv("PEER_NAME", "Bob"),
        PEER_URL=os.getenv("PEER_URL", "http://bob:8000"),
        PEER_TOKEN=os.getenv("PEER_TOKEN", "assignment2-local-demo"),
        E91_ROUNDS=int(os.getenv("E91_ROUNDS", "4096")),
        E91_SEED=None,
        MAX_MESSAGE_LENGTH=4096,
    )
    if config:
        app.config.update(config)

    state = PeerState()
    peer = transport or RequestsPeerTransport(
        app.config["PEER_URL"],
        app.config["PEER_TOKEN"],
    )
    app.extensions["peer_state"] = state
    app.extensions["peer_transport"] = peer

    def require_peer_token() -> tuple[Any, int] | None:
        supplied = request.headers.get("X-Peer-Token", "")
        if not secrets.compare_digest(supplied, app.config["PEER_TOKEN"]):
            return jsonify(error="Peer authentication failed."), 403
        return None

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            role=app.config["ROLE"],
            peer_name=app.config["PEER_NAME"],
            peer_url=app.config["PEER_URL"],
        )

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", role=app.config["ROLE"])

    @app.get("/api/messages")
    def api_messages():
        return jsonify(role=app.config["ROLE"], messages=state.messages())

    @app.get("/api/peer-status")
    def api_peer_status():
        try:
            response = peer.post("/internal/ping", {})
            return jsonify(connected=response.get("status") == "ok", peer=app.config["PEER_NAME"])
        except PeerConnectionError:
            return jsonify(connected=False, peer=app.config["PEER_NAME"])

    @app.post("/internal/ping")
    def internal_ping():
        rejected = require_peer_token()
        if rejected:
            return rejected
        return jsonify(status="ok", role=app.config["ROLE"])

    @app.post("/internal/settings")
    def internal_settings():
        rejected = require_peer_token()
        if rejected:
            return rejected
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        rounds = data.get("rounds")
        if not _valid_session_id(session_id):
            return jsonify(error="Invalid session ID."), 400
        if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds <= 0:
            return jsonify(error="Rounds must be a positive integer."), 400
        base_seed = app.config.get("E91_SEED")
        settings_seed = None if base_seed is None else int(base_seed) + 1
        settings = generate_bob_settings(rounds, seed=settings_seed)
        state.store_settings(session_id, settings)
        return jsonify(session_id=session_id, settings=settings)

    @app.post("/internal/session")
    def internal_session():
        rejected = require_peer_token()
        if rejected:
            return rejected
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        if not _valid_session_id(session_id):
            return jsonify(error="Invalid session ID."), 400
        settings = state.consume_settings(session_id)
        if settings is None:
            return jsonify(error="Unknown or expired session."), 404
        try:
            salt = bytes.fromhex(data["salt"])
            candidate_bits = receiver_candidate_bits(settings, data["receiver_rows"])
            key = derive_aes_key(candidate_bits, salt)
        except (KeyError, TypeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
        state.store_session(session_id, key)
        return jsonify(session_id=session_id, candidate_key_bits=len(candidate_bits))

    @app.post("/internal/messages")
    def internal_messages():
        rejected = require_peer_token()
        if rejected:
            return rejected
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        sender = data.get("sender")
        receiver = data.get("receiver")
        if not _valid_session_id(session_id) or sender != app.config["PEER_NAME"] or receiver != app.config["ROLE"]:
            return jsonify(error="Invalid message metadata."), 400
        key = state.consume_session(session_id)
        if key is None:
            return jsonify(error="Unknown or expired session key."), 404
        try:
            supplied_aad = bytes.fromhex(data["aad"])
            expected_aad = canonical_aad(session_id, sender, receiver)
            if not secrets.compare_digest(supplied_aad, expected_aad):
                raise ValueError("Authenticated metadata does not match the session.")
            payload = EncryptedPayload.from_dict(data["payload"])
            plaintext = decrypt_message(key, payload, expected_aad).decode("utf-8")
            metrics = data["metrics"]
            record = {
                "id": session_id,
                "direction": "received",
                "peer": sender,
                "plaintext": plaintext,
                "ciphertext_preview": payload.ciphertext.hex()[:64],
                "chsh": round(float(metrics["chsh"]), 4),
                "candidate_key_bits": int(metrics["candidate_key_bits"]),
                "key_error_rate": float(metrics["key_error_rate"]),
                "timestamp": _utc_now(),
            }
        except (InvalidTag, KeyError, TypeError, UnicodeDecodeError, ValueError) as exc:
            return jsonify(error=f"Message authentication failed: {exc}"), 400
        state.add_message(record)
        return jsonify(status="received", message=record)

    @app.post("/api/send")
    def api_send():
        data = request.get_json(silent=True) or {}
        message = data.get("message")
        if not isinstance(message, str) or not message.strip():
            return jsonify(error="Message must be a non-empty string."), 400
        message = message.strip()
        if len(message) > app.config["MAX_MESSAGE_LENGTH"]:
            return jsonify(error=f"Message must not exceed {app.config['MAX_MESSAGE_LENGTH']} characters."), 400

        session_id = uuid4().hex
        rounds = int(app.config["E91_ROUNDS"])
        try:
            settings_response = peer.post(
                "/internal/settings",
                {"session_id": session_id, "rounds": rounds},
            )
            bob_settings = settings_response["settings"]
            result = run_e91(rounds, bob_settings=bob_settings, seed=app.config.get("E91_SEED"))
            if not isfinite(result.chsh) or result.chsh <= 2.5:
                return jsonify(error="CHSH verification did not meet the demonstration threshold."), 409
            if len(result.alice_key_bits) < 256:
                return jsonify(error="The candidate key is shorter than 256 bits. Retry the session."), 409

            salt = secrets.token_bytes(16)
            receiver_rows = [
                {"alice_setting": item.alice_setting, "bob_bit": item.bob_bit}
                for item in result.rounds
            ]
            receiver_session = peer.post(
                "/internal/session",
                {
                    "session_id": session_id,
                    "salt": salt.hex(),
                    "receiver_rows": receiver_rows,
                },
            )
            if receiver_session["candidate_key_bits"] != len(result.alice_key_bits):
                return jsonify(error="Alice and Bob candidate-key lengths do not match."), 409

            aad = canonical_aad(session_id, app.config["ROLE"], app.config["PEER_NAME"])
            key = derive_aes_key(result.alice_key_bits, salt)
            payload = encrypt_message(key, message.encode("utf-8"), aad)
            metrics = {
                "chsh": result.chsh,
                "candidate_key_bits": len(result.alice_key_bits),
                "key_error_rate": result.key_error_rate,
            }
            peer.post(
                "/internal/messages",
                {
                    "session_id": session_id,
                    "sender": app.config["ROLE"],
                    "receiver": app.config["PEER_NAME"],
                    "aad": aad.hex(),
                    "payload": payload.to_dict(),
                    "metrics": metrics,
                },
            )
        except (KeyError, TypeError, ValueError, PeerConnectionError):
            return jsonify(error=f"Could not communicate with {app.config['PEER_NAME']}."), 502

        record = {
            "id": session_id,
            "direction": "sent",
            "peer": app.config["PEER_NAME"],
            "plaintext": message,
            "ciphertext_preview": payload.ciphertext.hex()[:64],
            "chsh": round(result.chsh, 4),
            "candidate_key_bits": len(result.alice_key_bits),
            "key_error_rate": result.key_error_rate,
            "timestamp": _utc_now(),
        }
        state.add_message(record)
        return jsonify(status="delivered", message=record)

    return app


app = create_app()
