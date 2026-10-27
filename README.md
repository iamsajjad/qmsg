# Assignment 2: E91, AES-GCM, and Superdense Coding

This project corrects and integrates the five assignment tasks:

1. Create and measure a Bell state.
2. Simulate E91-style entanglement measurements and a CHSH test.
3. Derive a 256-bit key and encrypt a message with AES-GCM.
4. Demonstrate superdense coding for all four two-bit messages.
5. Authenticate and decrypt the AES-GCM message.

It also provides two equal Quanta messaging pages. Alice and Bob can each send encrypted messages, view a shared conversation timeline, and follow an automatic educational sequence for every delivery.

## Important limitation

This is an educational simulator. Docker networking is classical, and the joint Qiskit simulation runs in the sending container. The project does not create physical entanglement and does not provide a production QKD system, authenticated classical-channel bootstrapping, information reconciliation, or full privacy amplification.

## Docker addresses and ports

| Connection | Address | Explanation |
|---|---|---|
| Browser to Alice | `http://localhost:8080` | Host port 8080 maps to Alice's container port 8000. |
| Browser to Bob | `http://localhost:8081` | Host port 8081 maps to Bob's container port 8000. |
| Alice to Bob | `http://bob:8000` | Docker resolves the service name `bob` to Bob's private container IP. |
| Bob to Alice | `http://alice:8000` | Docker resolves the service name `alice` to Alice's private container IP. |

Docker assigns private IP addresses dynamically. The applications use service names, so no fixed container IP address is required.

Inspect the current private addresses after startup:

```bash
docker compose exec alice getent hosts bob
docker compose exec bob getent hosts alice
```

## Run the two-container web demonstration

Start both containers:

```bash
docker compose up --build
```

Open both pages:

- Alice: <http://localhost:8080>
- Bob: <http://localhost:8081>

Type a message on either page and select **Send securely**. The learning rail advances automatically through entanglement, basis selection, measurement, CHSH verification, key derivation, encryption, delivery, and peer decryption. The receiver page refreshes automatically and shows the decrypted message in the conversation.

Stop the containers:

```bash
docker compose down
```

For a less predictable local demo token, set the same value for both services through Compose variable substitution:

```bash
PEER_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')" docker compose up --build
```

The token only protects the demo's internal HTTP endpoints. It does not turn the simulator into secure QKD.

## Run the five tasks locally

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

### 1. Bell-state measurement

```bash
python entangled_state.py --shots 1000 --seed 7
```

Only `00` and `11` occur in the ideal simulation.

### 2. E91 simulation

```bash
python e91.py --rounds 4096 --seed 19 --key-out e91_key.txt
```

The ideal CHSH magnitude is near `2.828`, the Alice and corrected Bob keys match, and the ideal key error rate is zero. The exact stochastic result varies when no seed is supplied.

### 3. AES-GCM encryption

```bash
python aes_encrypt.py "Hello Bob, this message is secret!" \
  --key-file e91_key.txt \
  --output encrypted.bin
```

The file contains a JSON envelope with public salt, authenticated data, nonce, and ciphertext with its authentication tag. It does not contain the AES key or E91 candidate bits.

### 4. Superdense coding

```bash
python superdense.py 11 --shots 100 --seed 5
```

Try `00`, `01`, `10`, and `11`. The ideal decoded result matches the selected input.

### 5. AES-GCM decryption

```bash
python aes_decrypt.py --key-file e91_key.txt --input encrypted.bin
```

Changing the key, nonce, authenticated data, authentication tag, or ciphertext makes decryption fail authentication.

## Run the tests

```bash
pytest -v
```

The tests cover Bell correlations, E91 sifting and CHSH, Qiskit bit ordering, AES authentication and tamper rejection, all four superdense messages, both Flask directions, and Docker Compose network configuration.

## Project layout

```text
Assignment2/
|-- app.py
|-- entangled_state.py
|-- e91.py
|-- aes_encrypt.py
|-- superdense.py
|-- aes_decrypt.py
|-- quanta/
|   |-- entanglement.py
|   |-- e91.py
|   |-- crypto.py
|   |-- superdense.py
|   `-- protocol.py
|-- templates/index.html
|-- static/app.css
|-- static/app.js
|-- static/protocol-sequence.js
|-- static/ui-state.js
|-- tests/
|-- Dockerfile
|-- compose.yaml
|-- requirements.txt
`-- pyproject.toml
```
