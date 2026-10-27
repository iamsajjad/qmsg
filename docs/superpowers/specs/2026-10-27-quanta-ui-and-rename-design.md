# Quanta UI and Project Rename Design

## Intent

Turn the existing two-container E91 and AES demonstration into a modern encrypted messaging application named **Quanta**. The primary experience remains a working Alice and Bob chat, while an educational rail explains how each message moves from entanglement through E91 verification, AES-GCM encryption, delivery, and decryption.

The interface is for an assignment demonstration. It should help a viewer understand both the messaging flow and the networking relationship between the two Docker containers without presenting the simulator as physical quantum communication.

## Goals

- Present Alice and Bob as equal messaging peers in a polished, responsive chat interface.
- Start the educational sequence when a message is submitted and advance it automatically.
- Show eight understandable stages: create entanglement, choose bases, measure qubits, verify CHSH, derive the AES key, encrypt the message, deliver ciphertext, and decrypt for the peer.
- Keep the final CHSH value, candidate-key length, key error rate, session identifier, and ciphertext preview available for learning.
- Preserve two-way messaging, peer health checks, automatic message refresh, API behavior, cryptographic behavior, and ports `8080` and `8081`.
- Standardize the Python package, Docker network, project metadata, documentation, and visible product branding as `quanta` or Quanta.
- Keep Docker service names `alice` and `bob`, because those names are the internal DNS addresses used for peer communication.

## Non-goals

- Do not add a physical quantum channel, production QKD security, user accounts, persistent storage, message attachments, or Internet-facing deployment features.
- Do not add fixed container IP addresses. Docker service-name discovery remains the communication mechanism.
- Do not change host or container ports.
- Do not add a frontend framework or a new JavaScript build process.
- Do not make superdense coding part of message delivery. It remains a separate assignment demonstration.

## Anti-goals

- Do not present time-based educational animation as live server telemetry.
- Do not expose candidate key bits, AES keys, peer tokens, or plaintext on the wire.
- Do not introduce non-functional navigation or decorative dashboard statistics.
- Do not hide errors behind a success animation.

## Constraints

- Existing stack: Flask, plain HTML, plain CSS, plain JavaScript, Qiskit, Cryptography, Gunicorn, Docker Compose.
- Both role pages use the same template and assets, with role and peer values supplied by Flask.
- The `/api/send` endpoint completes the quantum simulation, key derivation, encryption, peer delivery, and decryption before returning one response. The browser therefore cannot know the exact live server stage without a new streaming protocol.
- The educational sequence is an automatic explanation of the expected protocol order. It starts alongside the request, waits for the real response, and only enters the completed state after the response succeeds.
- Accessibility must include semantic controls, visible focus treatment, keyboard operation, readable contrast, `aria-live` updates, and reduced-motion support.
- The layout must reflow cleanly from desktop to a 320-pixel-wide viewport.

## Approaches Considered

### Chat plus learning rail, selected

Use a conversation-centered layout with a permanent educational rail beside the chat. The rail advances automatically while a message is being processed. This keeps the messaging task primary while explaining each protocol stage in context.

Tradeoff: the timed stage movement is explanatory, not exact server telemetry. The UI must say this clearly and use the actual API response as the success or failure authority.

### Guided protocol wizard

Make users advance through the protocol before reaching the chat. This gives more space to each concept but slows repeated messaging and makes the application feel like a slide deck instead of a messenger.

### Dashboard with protocol cards

Keep the current dashboard structure and add more animated metric cards. This is the smallest code change, but it separates the educational explanation from the message that caused it and adds visual noise.

## Selected Experience

### Application shell

- Top bar: Quanta mark, current conversation, peer identity, and connected or unreachable state.
- Left navigation on wide screens: real anchors to Messages, Learn, and Protocol details. It collapses on narrower screens.
- Center: one combined conversation timeline with sent messages aligned to the current role and received messages aligned to the peer.
- Bottom composer: single-line growing message field, clear send action, status feedback, and the existing 4096-character limit.
- Right rail: eight protocol stages, a progress track, the current plain-language explanation, and final metrics.
- Mobile: chat first, then the educational rail. All essential content remains visible without horizontal scrolling.

### Automatic sequence

1. The user submits a non-empty message.
2. The send button becomes disabled and the first stage becomes active.
3. The browser starts the existing `/api/send` request immediately.
4. The rail advances automatically through the first seven ordered educational stages at a readable pace.
5. If the request is still running, stage seven, deliver ciphertext, remains active in a waiting state and stage eight remains pending. This avoids implying that peer decryption has succeeded before the server confirms it.
6. On a successful response, stage eight, decrypt for the peer, becomes active for a brief explanatory beat and then every stage becomes complete. Actual E91 metrics populate, the composer clears, and the conversation refreshes.
7. On an error response, the animation stops, the current stage is marked as failed, the error is announced, the typed message remains available, and sending is re-enabled.
8. A received message appears through the existing polling refresh and can expand to show protocol details.

For reduced-motion users, stages update without motion and with shorter timing while preserving the ordered status changes.

### Educational accuracy

- The rail states that it is explaining the protocol sequence while the simulator runs.
- The final metrics come only from the server response.
- The completion state appears only after Bob has authenticated and decrypted the message.
- A persistent footer states that the project is an educational simulator without a physical quantum channel.

### Message presentation

- Sent and received records are merged into one time-ordered conversation.
- Each bubble includes direction, peer, timestamp, and an encrypted status.
- An expandable details section contains session ID, CHSH value, candidate-key length, key error rate, and ciphertext preview.
- Content is inserted using DOM text properties, not unsanitized HTML interpolation.

## Naming Migration

- Use `quanta/` as the Python package directory.
- Use `quanta` for all Python imports.
- Use `quanta` as the Compose network name.
- Use `assignment2-quanta` as the project package name.
- Update the Dockerfile package copy path, tests, README examples, project tree, titles, descriptions, and visible branding.
- Keep protocol wire value `assignment2-e91-aes-v1` unchanged. It is a versioned authenticated-data identifier, not visible product branding, and changing it provides no user benefit.
- Keep services `alice` and `bob` and their internal URLs `http://alice:8000` and `http://bob:8000` unchanged.

## Testing and Verification

- Update page tests to assert Quanta branding, equal Alice and Bob controls, the combined conversation, all eight learning stages, and simulator disclosure.
- Add frontend behavior tests for ordered automatic progression, successful completion, error preservation, safe DOM rendering, and reduced-motion handling. Use the smallest available JavaScript test method that does not add a production dependency.
- Update Compose tests to require the shared `quanta` bridge network and the unchanged service-name URLs and ports.
- Update import and CLI tests to use the `quanta` package.
- Run the full Python test suite.
- Run JavaScript syntax validation and the frontend behavior tests.
- Render both role pages at desktop and mobile widths for visual inspection.
- Validate the Compose configuration when Docker Compose is available. If Docker is unavailable in this environment, report that limitation instead of claiming a container build was verified.

## Builder Calls

- Use CSS and vanilla JavaScript only, because the current application does not have a frontend build pipeline.
- Keep the existing JSON API contract unless a test demonstrates that a small additive field is needed.
- Use the real API result as the authority for completion and failure.
- Hold the automatic animation at delivery while the request is pending. Advance to peer decryption only after the successful response.
- Prefer one responsive template over separate Alice and Bob templates.
- Preserve existing security boundaries and do not return key material to the browser.
