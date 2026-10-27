(function exposeUiState(globalScope, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (globalScope) {
    globalScope.QuantaUiState = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildUiState() {
  function messageListVersion(messages) {
    return JSON.stringify(messages.map((item) => [
      item.id,
      item.direction,
      item.peer,
      item.plaintext,
      item.ciphertext_preview,
      item.chsh,
      item.candidate_key_bits,
      item.key_error_rate,
      item.timestamp,
    ]));
  }

  function isNearConversationEnd(container, threshold = 80) {
    const remaining = container.scrollHeight - container.scrollTop - container.clientHeight;
    return remaining <= threshold;
  }

  return { isNearConversationEnd, messageListVersion };
});
