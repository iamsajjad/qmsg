const assert = require("node:assert/strict");
const test = require("node:test");

const {
  isNearConversationEnd,
  messageListVersion,
} = require("../../static/ui-state.js");


test("unchanged message lists have the same render version", () => {
  const messages = [{ id: "one", direction: "sent", plaintext: "Hello" }];

  assert.equal(messageListVersion(messages), messageListVersion([{ ...messages[0] }]));
});


test("a new or changed message has a different render version", () => {
  const original = [{ id: "one", direction: "sent", plaintext: "Hello" }];
  const updated = [
    ...original,
    { id: "two", direction: "received", plaintext: "Reply" },
  ];

  assert.notEqual(messageListVersion(original), messageListVersion(updated));
});


test("conversation is near the end only within the supplied threshold", () => {
  assert.equal(isNearConversationEnd({ scrollHeight: 1000, scrollTop: 620, clientHeight: 320 }), true);
  assert.equal(isNearConversationEnd({ scrollHeight: 1000, scrollTop: 300, clientHeight: 320 }), false);
});
