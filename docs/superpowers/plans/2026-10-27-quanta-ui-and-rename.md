# Quanta UI and Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Rename the educational application to Quanta and replace its dashboard with a responsive chat interface whose protocol rail advances automatically while the existing send request runs.

**Architecture:** Keep Flask routes, E91 logic, AES-GCM logic, message records, Docker services, internal DNS names, and ports unchanged. Rename only project identifiers and imports, then rebuild the shared template, CSS, and browser JavaScript around the existing JSON endpoints. A small dependency-free JavaScript state controller drives the explanatory sequence and is tested with Node's built-in test runner.

**Tech Stack:** Python 3.12, Flask, Jinja, vanilla JavaScript, CSS, pytest, Node built-in test runner, Docker Compose YAML

**Spec:** `docs/superpowers/specs/2026-10-27-quanta-ui-and-rename-design.md`

## Global Constraints

- Change only UI/UX and project naming.
- Do not change protocol, encryption, Flask API, message wire format, Docker service names, internal peer URLs, or ports.
- Keep Alice on `localhost:8080`, Bob on `localhost:8081`, and both containers on internal port `8000`.
- The automatic rail is explanatory; the real `/api/send` response is the authority for success or failure.
- Do not expose key material in the UI or API.
- Do not add production dependencies or a frontend build process.

## Review Focus

- An empty or whitespace-only composer submission must not start the sequence or request.
- A failed request must keep the typed message, show the error, stop progression, and re-enable send.
- A slow request must wait at delivery and must not show peer decryption before success.
- Message text containing HTML must render as text, not executable markup.
- Mobile widths and reduced-motion preferences must retain all content and ordered status updates.

---

### Task 1: Quanta naming migration

**Files:**
- Rename: existing Python package directory to `quanta/`
- Modify: `app.py`
- Modify: `entangled_state.py`
- Modify: `e91.py`
- Modify: `aes_encrypt.py`
- Modify: `aes_decrypt.py`
- Modify: `superdense.py`
- Modify: `Dockerfile`
- Modify: `compose.yaml`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `tests/test_*.py`
- Create: `tests/test_project_identity.py`

**Interfaces:**
- Produces: importable `quanta` package with the same public Python interfaces as the legacy package.
- Produces: Compose network `quanta`; services, URLs, and ports remain unchanged.
- Consumes: no new application interfaces.

- [x] **Step 1: Write failing identity and Compose tests**

Add `test_quanta_package_is_importable()` and `test_project_metadata_uses_quanta_name()` with literal expected names. Update the existing Compose network test to expect `quanta` while still asserting services `alice` and `bob`, their DNS URLs, and ports.

- [x] **Step 2: Run the focused tests and verify RED**

Run: `.venv/bin/pytest tests/test_project_identity.py tests/test_compose_config.py -q`

Expected: FAIL because the `quanta` package and network do not yet exist.

- [x] **Step 3: Apply the naming migration**

Rename the package directory and update imports, Dockerfile copy path, Compose network, package metadata, tests, README, and active project documentation. Remove only the stale generated legacy egg-info directory if present.

- [x] **Step 4: Run the focused tests and full suite**

Run: `.venv/bin/pytest tests/test_project_identity.py tests/test_compose_config.py -q && .venv/bin/pytest -q`

Expected: focused tests pass and the full suite passes.

- [x] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: rename project to Quanta"
```

### Task 2: Responsive chat and automatic learning rail

**Files:**
- Modify: `templates/index.html`
- Modify: `static/app.css`
- Modify: `static/app.js`
- Create: `static/protocol-sequence.js`
- Create: `tests/js/protocol-sequence.test.js`
- Modify: `tests/test_apps.py`

**Interfaces:**
- Consumes: unchanged `/api/messages`, `/api/peer-status`, and `/api/send` JSON endpoints.
- Produces: `window.QuantaProtocol.createProtocolSequence(options)` for browser use and the same export for Node tests.
- Produces: DOM targets `#conversation`, `#message-form`, `#message`, `#send-message`, `#action-note`, `#peer-status`, `#protocol-progress`, and eight `[data-protocol-step]` elements.

- [x] **Step 1: Write failing page-structure tests**

Update `test_both_role_pages_have_equal_messaging_controls()` to require Quanta branding, a combined conversation, the composer, all eight named stages, protocol metrics, simulator disclosure, and the unchanged role and peer names.

- [x] **Step 2: Run the page test and verify RED**

Run: `.venv/bin/pytest tests/test_apps.py::test_both_role_pages_have_equal_messaging_controls -q`

Expected: FAIL because the current dashboard does not contain the Quanta chat shell or eight-stage rail.

- [x] **Step 3: Write failing sequence-controller tests**

Add Node tests that use a fake scheduler to verify: start advances only through stage seven, a pending request waits at delivery, success activates stage eight before completion, failure stops progression and preserves the failure message, and reset returns to ready.

- [x] **Step 4: Run the JavaScript tests and verify RED**

Run: `node --test tests/js/protocol-sequence.test.js`

Expected: FAIL because `static/protocol-sequence.js` does not exist.

- [x] **Step 5: Implement the UI and sequence controller**

Build the approved responsive shell in the shared Jinja template and CSS. Implement the dependency-free sequence controller, load it before `app.js`, and integrate it with the existing requests. Render message records with DOM `textContent`, merge them into one conversation, keep polling, preserve input on errors, and populate metrics only from successful server data.

- [x] **Step 6: Run focused checks and refactor while green**

Run: `node --test tests/js/protocol-sequence.test.js && node --check static/protocol-sequence.js && node --check static/app.js && .venv/bin/pytest tests/test_apps.py -q`

Expected: all JavaScript tests, syntax checks, and Flask application tests pass.

- [x] **Step 7: Run the complete verification suite**

Run: `.venv/bin/pytest -q && node --test tests/js/protocol-sequence.test.js && node --check static/protocol-sequence.js && node --check static/app.js`

Expected: all checks pass with zero failures.

- [x] **Step 8: Commit**

```bash
git add templates/index.html static/app.css static/app.js static/protocol-sequence.js tests/test_apps.py tests/js/protocol-sequence.test.js
git commit -m "feat: add Quanta messaging experience"
```
