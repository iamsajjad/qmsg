# E91, AES, and Docker Demo Design

## Intent

Create a corrected, self-contained Assignment 2 project that demonstrates Bell-state entanglement, simulated E91 key establishment, AES-256-GCM encryption and decryption, and superdense coding. Add matching Flask pages where Alice and Bob can send authenticated ciphertext to each other across a two-container Docker Compose network and see both sides of the exchange.

## Goals

- Replace the malformed pasted Python with runnable, importable code.
- Implement an ideal E91 simulation using the singlet state, randomized measurement settings, a CHSH test, key sifting, and Bob bit correction.
- Derive equal 256-bit AES keys independently from Alice and Bob candidate keys with HKDF-SHA256.
- Encrypt with AES-GCM using a fresh 12-byte nonce and authenticated session metadata.
- Demonstrate all four superdense coding messages.
- Provide matching Flask interfaces hosted by Alice and Bob.
- Support encrypted messages in both directions.
- Connect Alice and Bob through Docker service-name DNS and symmetric internal peer APIs.
- Test quantum, cryptographic, network, and user-visible behavior.

## Non-goals

- Physical quantum communication or quantum hardware.
- A production QKD security claim.
- Authenticated classical-channel bootstrapping, information reconciliation, or full privacy amplification.
- Publishing Bob's API directly to the host.

## Constraints

- Exactly two long-running services: `alice` and `bob`.
- Both services listen on container port `8000`.
- Alice is published as host port `8080`; Bob is published as host port `8081`.
- Alice reaches Bob at `http://bob:8000`, and Bob reaches Alice at `http://alice:8000`; container IP addresses remain dynamic.
- Superdense coding remains an independent assignment task, not part of E91 or AES.
- The README must label the E91 portion as an educational simulation.

## Architecture

The shared Python package contains the Bell-state circuits, E91 simulator, HKDF and AES helpers, superdense coding functions, and a role-configured Flask application factory. Both services host the same browser page and peer API. For each message, the sender coordinates a new session, while the receiver creates independent measurement choices, receives only its simulated outcomes and public session data, derives its key, and decrypts the AES-GCM payload. The sender derives its key from its own retained outcomes. Both pages display their local message history and protocol metrics.

The simulation runs the joint quantum circuits inside Alice because Docker containers cannot exchange physical qubits. The code treats the joint simulator as the educational entanglement source and clearly documents that this central knowledge is not a secure QKD deployment.

## Network Flow

1. A browser opens Alice at `localhost:8080` or Bob at `localhost:8081`.
2. Docker forwards the request to the selected container's port `8000`.
3. The sending peer requests randomized settings from the receiving peer over the private Compose network.
4. The sender simulates paired measurements and sends the receiver only its outcomes plus public sifting data.
5. Both peers derive matching AES keys from their separate candidate bit strings.
6. The sender delivers the AES-GCM payload to the receiver's internal port `8000`.
7. The receiver authenticates, decrypts, and stores the message. Both browser pages show their local sent or received record.

## Approaches Considered

- Integrated two-container simulation, selected: preserves the assignment flow and demonstrates real container networking while stating its limitations.
- Pre-shared key: simpler, but does not connect E91 output to AES.
- Three-container source, Alice, and Bob model: clearer role separation, but conflicts with the two-container requirement.

## User Interface

The approved visual style is used on both pages. Each page contains its role and peer status, a message field, one send button, four protocol stages, CHSH and candidate-key metrics, sent and received message history, ciphertext details, and collapsible technical details. It does not expose the derived secret key.
