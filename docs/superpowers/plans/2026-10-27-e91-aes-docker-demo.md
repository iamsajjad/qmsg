# E91, AES, and Docker Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Assignment 2 project that links simulated E91 key establishment to AES-256-GCM and demonstrates two-way Alice and Bob communication through two Docker containers with matching Flask pages.

**Architecture:** A focused `quanta` package supplies quantum and cryptographic behavior. A role-configured Flask application runs in both containers. The sending peer coordinates each simulated session; the receiving peer owns its measurement settings and key derivation, decrypts the message, and stores the received record. Docker Compose provides service-name DNS and publishes both pages on different host ports.

**Tech Stack:** Python 3.12, Qiskit, Qiskit Aer, cryptography, Flask, pytest, Docker Compose

**Spec:** `docs/superpowers/specs/2026-10-27-e91-aes-docker-demo-design.md`

## Global Constraints

- Use the singlet Bell state and measurement settings that produce an ideal CHSH magnitude near `2 * sqrt(2)`.
- Parse Qiskit measurement strings explicitly as classical bit 1 for Bob and classical bit 0 for Alice.
- Use HKDF-SHA256 to derive 32-byte AES keys from packed candidate bits and a public per-session salt.
- Use AES-GCM with a unique 12-byte nonce and authenticated session metadata.
- Publish Alice as `8080:8000` and Bob as `8081:8000`; use `alice:8000` and `bob:8000` for private peer traffic.
- Do not present the simulator as physically secure QKD.

## Review Focus

- Qiskit endianness: a test must prove Alice and Bob outcomes are mapped from the intended classical bits.
- CHSH sign convention: a seeded ideal run must exceed the classical bound without requiring an exact stochastic value.
- Empty or short candidate key: key derivation must reject insufficient input with a clear error.
- AES tampering: modified ciphertext, nonce, or authenticated data must fail authentication.
- Peer unavailable: either page must return a useful error without disclosing a traceback.

---

### Task 1: Project skeleton and Bell-state demonstration

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `quanta/__init__.py`
- Create: `quanta/entanglement.py`
- Create: `entangled_state.py`
- Test: `tests/test_entanglement.py`

**Interfaces:**
- Produces: `build_phi_plus_circuit(measure: bool = True) -> QuantumCircuit`
- Produces: `measure_phi_plus(shots: int, seed: int | None = None) -> dict[str, int]`

- [ ] **Step 1: Write failing Bell-state tests**

Test that only `00` and `11` occur in an ideal simulation, their counts total the requested shots, and invalid shot counts are rejected.

- [ ] **Step 2: Run the tests and verify RED**

Run: `pytest tests/test_entanglement.py -v`

Expected: FAIL because `quanta.entanglement` does not exist.

- [ ] **Step 3: Implement the minimal Bell-state module and CLI**

Use `H(0)`, `CX(0, 1)`, explicit measurement, `AerSimulator`, and transpilation for the simulator target.

- [ ] **Step 4: Run the tests and verify GREEN**

Run: `pytest tests/test_entanglement.py -v`

Expected: all tests pass.

### Task 2: E91 simulation and CHSH analysis

**Files:**
- Create: `quanta/e91.py`
- Create: `e91.py`
- Test: `tests/test_e91.py`

**Interfaces:**
- Produces: `E91Settings`, `E91Round`, and `E91Result` dataclasses.
- Produces: `generate_bob_settings(rounds: int, seed: int | None = None) -> list[str]`
- Produces: `run_e91(rounds: int, bob_settings: list[str] | None = None, seed: int | None = None) -> E91Result`
- Produces: `bob_candidate_bits(result: E91Result) -> str`
- Produces: `calculate_chsh(rounds: Sequence[E91Round]) -> float`

- [ ] **Step 1: Write failing E91 tests**

Test singlet anticorrelation in the key basis, Qiskit bit ordering, independent setting input, matching Alice and corrected Bob candidate bits, zero ideal key error, and seeded `abs(S) > 2.5` with adequate test samples.

- [ ] **Step 2: Run the E91 tests and verify RED**

Run: `pytest tests/test_e91.py -v`

Expected: FAIL because the E91 module does not exist.

- [ ] **Step 3: Implement the minimal E91 simulator**

Prepare `|Psi->`, rotate each measurement basis with `RY`, batch circuits by basis pair, reconstruct ordered rounds from simulator memory, sift key rounds, and compute the four CHSH correlations.

- [ ] **Step 4: Run the E91 tests and verify GREEN**

Run: `pytest tests/test_e91.py -v`

Expected: all tests pass.

### Task 3: Key derivation and AES-GCM

**Files:**
- Create: `quanta/crypto.py`
- Create: `aes_encrypt.py`
- Create: `aes_decrypt.py`
- Test: `tests/test_crypto.py`

**Interfaces:**
- Produces: `pack_bits(bits: str) -> bytes`
- Produces: `derive_aes_key(bits: str, salt: bytes, info: bytes = b"assignment2-e91-aes-v1") -> bytes`
- Produces: `encrypt_message(key: bytes, plaintext: bytes, aad: bytes) -> EncryptedPayload`
- Produces: `decrypt_message(key: bytes, payload: EncryptedPayload, aad: bytes) -> bytes`
- Produces: JSON-safe `EncryptedPayload` serialization without including the key.

- [ ] **Step 1: Write failing cryptographic tests**

Test deterministic equal-key derivation, different salt separation, input validation, AES round-trip, unique nonce generation, and `InvalidTag` for modified ciphertext, nonce, AAD, or key.

- [ ] **Step 2: Run the crypto tests and verify RED**

Run: `pytest tests/test_crypto.py -v`

Expected: FAIL because the crypto module does not exist.

- [ ] **Step 3: Implement minimal HKDF and AES-GCM helpers**

Pack the exact bit length into the key material, use a 16-byte random salt, use `AESGCM`, and keep the 16-byte tag appended to ciphertext as returned by the library.

- [ ] **Step 4: Run the crypto tests and verify GREEN**

Run: `pytest tests/test_crypto.py -v`

Expected: all tests pass.

### Task 4: Superdense coding

**Files:**
- Create: `quanta/superdense.py`
- Create: `superdense.py`
- Test: `tests/test_superdense.py`

**Interfaces:**
- Produces: `build_superdense_circuit(bits: str) -> QuantumCircuit`
- Produces: `decode_superdense(bits: str, shots: int = 100, seed: int | None = None) -> dict[str, int]`

- [ ] **Step 1: Write failing superdense tests**

Test exact ideal decoding for `00`, `01`, `10`, and `11`, plus rejection of every invalid two-bit input.

- [ ] **Step 2: Run the tests and verify RED**

Run: `pytest tests/test_superdense.py -v`

Expected: FAIL because the superdense module does not exist.

- [ ] **Step 3: Implement minimal encoding and decoding**

Prepare `|Phi+>`, apply `Z` for the first classical bit and `X` for the second, decode with `CX` and `H`, and print the verified decoded result in the CLI.

- [ ] **Step 4: Run the tests and verify GREEN**

Run: `pytest tests/test_superdense.py -v`

Expected: all tests pass.

### Task 5: Symmetric peer API and matching web applications

**Files:**
- Create: `quanta/protocol.py`
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/app.css`
- Create: `static/app.js`
- Test: `tests/test_protocol.py`
- Test: `tests/test_apps.py`

**Interfaces:**
- Peer `POST /internal/settings`: accepts round count and session ID, returns the receiving peer's randomized measurement settings.
- Peer `POST /internal/session`: accepts receiver outcomes plus public sifting metadata, derives and temporarily stores the session key.
- Peer `POST /internal/messages`: accepts salt, nonce, ciphertext, and AAD, authenticates and decrypts the payload, stores a received record, and deletes the session key.
- Peer `GET /`: renders the same approved page with role-specific labels.
- Peer `POST /api/send`: validates the message, coordinates E91 with the configured peer, encrypts the message, delivers it, and stores a sent record.
- Peer `GET /api/messages`: returns the local sent and received records without secret keys.

- [ ] **Step 1: Write failing protocol and Flask tests**

Use two Flask test clients with in-process peer adapters to test settings ownership, equal keys, session cleanup, matching Alice and Bob pages, both message directions, message validation, peer connection failure, and no secret key in any response.

- [ ] **Step 2: Run the app tests and verify RED**

Run: `pytest tests/test_protocol.py tests/test_apps.py -v`

Expected: FAIL because the protocol and Flask applications do not exist.

- [ ] **Step 3: Implement Bob's internal endpoints and Alice's coordinator**

Store sessions and local message history in bounded in-memory dictionaries with timestamps, validate JSON shapes and lengths, and use request timeouts for every peer call.

- [ ] **Step 4: Implement the approved responsive page**

Render the same interface for both roles, including peer connection state, message form, protocol steps, CHSH value, candidate-key length, key error rate, ciphertext preview, sent and received history, and technical details without exposing key bytes.

- [ ] **Step 5: Run the app tests and verify GREEN**

Run: `pytest tests/test_protocol.py tests/test_apps.py -v`

Expected: all tests pass.

### Task 6: Docker packaging, documentation, and end-to-end verification

**Files:**
- Create: `Dockerfile`
- Create: `compose.yaml`
- Create: `.dockerignore`
- Create: `README.md`
- Test: `tests/test_compose_config.py`

**Interfaces:**
- Produces: Alice at `http://localhost:8080`.
- Produces: Bob at `http://localhost:8081`.
- Produces: private peer URLs `http://alice:8000` and `http://bob:8000`.

- [ ] **Step 1: Write a failing Compose configuration test**

Test that exactly `alice` and `bob` services exist, Alice publishes `8080:8000`, Bob publishes `8081:8000`, both receive the correct peer URL, and both services use the same private network.

- [ ] **Step 2: Run the Compose test and verify RED**

Run: `pytest tests/test_compose_config.py -v`

Expected: FAIL because `compose.yaml` does not exist.

- [ ] **Step 3: Add the container image and Compose configuration**

Use one image, role-specific environment values, health checks, a non-root runtime user, and dependency health ordering. Do not hard-code container IP addresses.

- [ ] **Step 4: Write the assignment README**

Document installation, local commands, Docker commands, both page URLs, IP and port behavior, two-way messaging, expected results, troubleshooting, and the security limitations of the simulation.

- [ ] **Step 5: Run the complete local verification suite**

Run: `pytest -v`

Expected: all tests pass with no warnings from project code.

- [ ] **Step 6: Validate Docker Compose and run the end-to-end demo**

Run: `docker compose config --quiet`

Expected: exit code 0.

Run: `docker compose up --build -d`, wait for both health checks, send Alice-to-Bob through port `8080`, send Bob-to-Alice through port `8081`, verify both pages report the received plaintext, then run `docker compose down`.

Expected: both directions return a CHSH violation, matching candidate-key metadata, authenticated AES-GCM delivery, and the original plaintext at the receiving peer.

- [ ] **Step 7: Create the final project archive**

Create `Assignment2-e91-aes-docker.zip` containing source, tests, Docker files, and documentation, excluding caches and generated ciphertext.
