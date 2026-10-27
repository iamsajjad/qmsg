const form = document.querySelector("#message-form");
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send-message");
const actionNote = document.querySelector("#action-note");
const conversation = document.querySelector("#conversation");
const statusBadge = document.querySelector("#peer-status");
const protocolProgress = document.querySelector("#protocol-progress");
const protocolProgressBar = document.querySelector("#protocol-progress-bar");
const protocolStatus = document.querySelector("#protocol-status");
const protocolCount = document.querySelector("#protocol-count");
const protocolSteps = [...document.querySelectorAll("[data-protocol-step]")];
const peerName = document.body.dataset.peer;
const roleName = document.body.dataset.role;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const timing = window.QuantaProtocol.getSequenceTiming(reducedMotion);
let renderedMessageVersion = null;


function appendDefinition(list, term, value) {
  const row = document.createElement("div");
  const name = document.createElement("dt");
  const description = document.createElement("dd");
  name.textContent = term;
  description.textContent = value;
  row.append(name, description);
  list.append(row);
}


function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}


function createMessage(item, openMessageIds) {
  const article = document.createElement("article");
  article.className = `message ${item.direction === "sent" ? "message-sent" : "message-received"}`;

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = item.direction === "sent" ? roleName.charAt(0) : String(item.peer).charAt(0);

  const content = document.createElement("div");
  content.className = "message-content";
  const bubble = document.createElement("p");
  bubble.className = "message-bubble";
  bubble.textContent = item.plaintext;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const sender = document.createElement("span");
  sender.textContent = item.direction === "sent" ? `${roleName} · encrypted` : `${item.peer} · decrypted`;
  const time = document.createElement("time");
  time.dateTime = item.timestamp;
  time.textContent = formatTimestamp(item.timestamp);
  meta.append(sender, time);

  const details = document.createElement("details");
  details.className = "message-details";
  details.dataset.messageId = item.id;
  details.open = openMessageIds.has(item.id);
  const summary = document.createElement("summary");
  summary.textContent = "View protocol details";
  const list = document.createElement("dl");
  appendDefinition(list, "Session", item.id);
  appendDefinition(list, "CHSH S", Number(item.chsh).toFixed(4));
  appendDefinition(list, "Candidate key", `${Number(item.candidate_key_bits)} bits`);
  appendDefinition(list, "Error rate", `${(Number(item.key_error_rate) * 100).toFixed(2)}%`);
  appendDefinition(list, "Ciphertext", `${item.ciphertext_preview}…`);
  details.append(summary, list);

  content.append(bubble, meta, details);
  article.append(avatar, content);
  return article;
}


function renderEmptyConversation() {
  const empty = document.createElement("div");
  empty.className = "empty-state";
  const symbol = document.createElement("span");
  symbol.setAttribute("aria-hidden", "true");
  symbol.textContent = "✦";
  const heading = document.createElement("strong");
  heading.textContent = "Your secure conversation starts here";
  const copy = document.createElement("p");
  copy.textContent = "Send a message to watch each E91 and AES step.";
  empty.append(symbol, heading, copy);
  conversation.replaceChildren(empty);
}


async function refreshMessages() {
  try {
    const response = await fetch("/api/messages");
    if (!response.ok) throw new Error("Could not refresh messages.");
    const data = await response.json();
    const messages = [...data.messages].sort((left, right) =>
      String(left.timestamp).localeCompare(String(right.timestamp))
    );
    const nextVersion = window.QuantaUiState.messageListVersion(messages);
    if (nextVersion === renderedMessageVersion) return;

    const firstRender = renderedMessageVersion === null;
    const shouldScrollToEnd = firstRender || window.QuantaUiState.isNearConversationEnd(conversation);
    const previousScrollTop = conversation.scrollTop;
    const openMessageIds = new Set(
      [...conversation.querySelectorAll("details[data-message-id][open]")]
        .map((details) => details.dataset.messageId)
    );
    renderedMessageVersion = nextVersion;
    if (!messages.length) {
      renderEmptyConversation();
      return;
    }
    conversation.replaceChildren(...messages.map((item) => createMessage(item, openMessageIds)));
    conversation.scrollTop = shouldScrollToEnd ? conversation.scrollHeight : previousScrollTop;
  } catch {
    if (!conversation.children.length) renderEmptyConversation();
  }
}


function setPeerStatus(connected) {
  statusBadge.classList.toggle("offline", !connected);
  const dot = document.createElement("span");
  dot.className = "status-dot";
  dot.setAttribute("aria-hidden", "true");
  statusBadge.replaceChildren(
    dot,
    document.createTextNode(connected ? `Connected to ${peerName}` : `Cannot reach ${peerName}`)
  );
}


async function refreshPeerStatus() {
  try {
    const response = await fetch("/api/peer-status");
    const data = await response.json();
    setPeerStatus(Boolean(response.ok && data.connected));
  } catch {
    setPeerStatus(false);
  }
}


function renderProtocolState(state) {
  protocolSteps.forEach((step, index) => {
    const isComplete = state.phase === "completed" || index < state.index;
    const isCurrent = index === state.index && !["ready", "completed"].includes(state.phase);
    step.classList.toggle("complete", isComplete);
    step.classList.toggle("current", isCurrent);
    step.classList.toggle("failed", isCurrent && state.phase === "failed");
    const detail = step.querySelector("p");
    detail.textContent = isCurrent ? step.dataset.description : "";
  });

  const visibleProgress = state.index < 0
    ? 0
    : state.phase === "completed"
      ? protocolSteps.length
      : Math.min(state.index + 1, protocolSteps.length);
  const completedCount = state.phase === "completed"
    ? protocolSteps.length
    : Math.max(0, state.index);
  protocolProgressBar.style.width = `${(visibleProgress / protocolSteps.length) * 100}%`;
  protocolProgress.setAttribute("aria-valuenow", String(visibleProgress));
  protocolCount.textContent = `${completedCount} / ${protocolSteps.length}`;

  if (state.phase === "ready") {
    protocolStatus.textContent = "Ready to send";
  } else if (state.phase === "waiting") {
    protocolStatus.textContent = "Waiting for peer confirmation";
  } else if (state.phase === "completed") {
    protocolStatus.textContent = "Delivered securely";
  } else if (state.phase === "failed") {
    protocolStatus.textContent = state.message;
  } else {
    protocolStatus.textContent = protocolSteps[state.index].querySelector("strong").textContent;
  }
}


const protocolSequence = window.QuantaProtocol.createProtocolSequence({
  onChange: renderProtocolState,
  stepDelay: timing.stepDelay,
  finalDelay: timing.finalDelay,
});


form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  sendButton.disabled = true;
  actionNote.classList.remove("error");
  actionNote.textContent = "Securing and delivering your message…";
  protocolSequence.start();

  try {
    const response = await fetch("/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Delivery failed.");

    document.querySelector("#metric-chsh").textContent = `${Number(data.message.chsh).toFixed(4)} · passed`;
    document.querySelector("#metric-key-bits").textContent = `${data.message.candidate_key_bits} bits`;
    document.querySelector("#metric-error").textContent = `${(Number(data.message.key_error_rate) * 100).toFixed(2)}%`;
    messageInput.value = "";
    actionNote.textContent = `${peerName} authenticated and decrypted the message.`;
    protocolSequence.succeed();
    await refreshMessages();
  } catch (error) {
    const messageText = error instanceof Error ? error.message : "Delivery failed.";
    actionNote.classList.add("error");
    actionNote.textContent = messageText;
    protocolSequence.fail(messageText);
  } finally {
    sendButton.disabled = false;
    messageInput.focus();
  }
});


messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 144)}px`;
});


renderProtocolState({ index: -1, phase: "ready", message: "" });
refreshMessages();
refreshPeerStatus();
window.setInterval(refreshMessages, 3000);
window.setInterval(refreshPeerStatus, 5000);
