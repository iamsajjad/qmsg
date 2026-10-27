from __future__ import annotations

from dataclasses import dataclass

import pytest

from app import create_app
from quanta.protocol import PeerConnectionError


@dataclass
class LocalPeerTransport:
    token: str
    client: object | None = None

    def post(self, path: str, payload: dict) -> dict:
        if self.client is None:
            raise PeerConnectionError("peer is unavailable")
        response = self.client.post(
            path,
            json=payload,
            headers={"X-Peer-Token": self.token},
        )
        if response.status_code >= 400:
            raise PeerConnectionError(response.get_json()["error"])
        return response.get_json()


@pytest.fixture
def peer_apps():
    token = "test-peer-token"
    alice_transport = LocalPeerTransport(token)
    bob_transport = LocalPeerTransport(token)
    common = {
        "TESTING": True,
        "PEER_TOKEN": token,
        "E91_ROUNDS": 4096,
        "E91_SEED": 31,
    }
    alice = create_app(
        {**common, "ROLE": "Alice", "PEER_NAME": "Bob", "PEER_URL": "http://bob:8000"},
        transport=alice_transport,
    )
    bob = create_app(
        {**common, "ROLE": "Bob", "PEER_NAME": "Alice", "PEER_URL": "http://alice:8000"},
        transport=bob_transport,
    )
    alice_client = alice.test_client()
    bob_client = bob.test_client()
    alice_transport.client = bob_client
    bob_transport.client = alice_client
    return alice_client, bob_client


def test_both_role_pages_have_equal_quanta_messaging_experience(peer_apps):
    alice, bob = peer_apps

    alice_html = alice.get("/").get_data(as_text=True)
    bob_html = bob.get("/").get_data(as_text=True)

    for html, role, peer in ((alice_html, "Alice", "Bob"), (bob_html, "Bob", "Alice")):
        assert f"{role} | Quanta" in html
        assert "Quanta" in html
        assert f"{role} ↔ {peer}" in html
        assert f"Secure conversation with {peer}" in html
        assert 'id="message"' in html
        assert 'id="send-message"' in html
        assert 'aria-label="Send securely"' in html
        assert 'id="conversation"' in html
        assert 'id="protocol-rail"' in html
        assert 'id="protocol-progress"' in html
        assert 'id="metric-chsh"' in html
        assert 'id="metric-key-bits"' in html
        assert 'id="metric-error"' in html
        assert 'src="/static/protocol-sequence.js"' in html
        assert html.count("data-protocol-step") == 8
        for stage in (
            "Create entanglement",
            "Choose bases",
            "Measure qubits",
            "Verify CHSH",
            "Derive AES key",
            "Encrypt message",
            "Deliver ciphertext",
            f"Decrypt for {peer}",
        ):
            assert stage in html
        assert "Educational simulator" in html
        assert "No physical quantum channel" in html


def test_alice_can_send_and_bob_can_receive(peer_apps):
    alice, bob = peer_apps

    response = alice.post("/api/send", json={"message": "Hello from Alice"})

    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "delivered"
    assert result["message"]["plaintext"] == "Hello from Alice"
    assert result["message"]["direction"] == "sent"
    assert result["message"]["chsh"] > 2.5
    assert result["message"]["candidate_key_bits"] >= 256
    assert "key" not in result

    bob_messages = bob.get("/api/messages").get_json()["messages"]
    assert bob_messages[0]["direction"] == "received"
    assert bob_messages[0]["plaintext"] == "Hello from Alice"
    assert bob_messages[0]["peer"] == "Alice"
    assert {"raw_key", "aes_key", "key_bytes", "candidate_bits"}.isdisjoint(bob_messages[0])


def test_bob_can_send_and_alice_can_receive(peer_apps):
    alice, bob = peer_apps

    response = bob.post("/api/send", json={"message": "Reply from Bob"})

    assert response.status_code == 200
    alice_messages = alice.get("/api/messages").get_json()["messages"]
    assert alice_messages[0]["direction"] == "received"
    assert alice_messages[0]["plaintext"] == "Reply from Bob"
    assert alice_messages[0]["peer"] == "Bob"


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": "   "}, {"message": 3}])
def test_send_rejects_invalid_messages(peer_apps, payload):
    alice, _ = peer_apps

    response = alice.post("/api/send", json=payload)

    assert response.status_code == 400
    assert "message" in response.get_json()["error"].lower()


def test_internal_endpoints_require_peer_token(peer_apps):
    _, bob = peer_apps

    response = bob.post("/internal/settings", json={"session_id": "x", "rounds": 4096})

    assert response.status_code == 403


def test_sender_reports_peer_connection_failure_without_traceback():
    app = create_app(
        {
            "TESTING": True,
            "ROLE": "Alice",
            "PEER_NAME": "Bob",
            "PEER_URL": "http://bob:8000",
            "PEER_TOKEN": "token",
            "E91_ROUNDS": 4096,
        },
        transport=LocalPeerTransport("token"),
    )

    response = app.test_client().post("/api/send", json={"message": "Hello"})

    assert response.status_code == 502
    body = response.get_json()
    assert body == {"error": "Could not communicate with Bob."}
    assert "traceback" not in response.get_data(as_text=True).lower()


def test_sender_rejects_non_finite_chsh_before_key_length_check():
    token = "test-peer-token"
    alice_transport = LocalPeerTransport(token)
    bob_transport = LocalPeerTransport(token)
    common = {
        "TESTING": True,
        "PEER_TOKEN": token,
        "E91_ROUNDS": 1,
        "E91_SEED": 7,
    }
    alice = create_app(
        {**common, "ROLE": "Alice", "PEER_NAME": "Bob", "PEER_URL": "http://bob:8000"},
        transport=alice_transport,
    )
    bob = create_app(
        {**common, "ROLE": "Bob", "PEER_NAME": "Alice", "PEER_URL": "http://alice:8000"},
        transport=bob_transport,
    )
    alice_transport.client = bob.test_client()
    bob_transport.client = alice.test_client()

    response = alice.test_client().post("/api/send", json={"message": "Hello"})

    assert response.status_code == 409
    assert "CHSH" in response.get_json()["error"]
