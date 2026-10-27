const assert = require("node:assert/strict");
const test = require("node:test");

const {
  createProtocolSequence,
  getSequenceTiming,
} = require("../../static/protocol-sequence.js");


function createFakeScheduler() {
  let pending = [];

  return {
    schedule(callback, delay) {
      const task = { callback, delay };
      pending.push(task);
      return task;
    },
    cancel(task) {
      pending = pending.filter((candidate) => candidate !== task);
    },
    runNext() {
      const task = pending.shift();
      assert.ok(task, "expected a scheduled protocol transition");
      task.callback();
    },
    runAll() {
      while (pending.length) this.runNext();
    },
    count() {
      return pending.length;
    },
  };
}


test("automatic progression waits at delivery while the request is pending", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
    stepDelay: 10,
    finalDelay: 5,
  });

  sequence.start();
  scheduler.runAll();

  assert.deepEqual(states.map((state) => state.index), [0, 1, 2, 3, 4, 5, 6]);
  assert.equal(states.at(-1).phase, "waiting");
  assert.equal(scheduler.count(), 0);
});


test("success activates peer decryption before completing", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
    stepDelay: 10,
    finalDelay: 5,
  });

  sequence.start();
  scheduler.runAll();
  sequence.succeed();

  assert.deepEqual(states.at(-1), { index: 7, phase: "decrypting", message: "" });
  scheduler.runNext();
  assert.deepEqual(states.at(-1), { index: 7, phase: "completed", message: "" });
});


test("an early success response still presents every stage in order", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
    stepDelay: 10,
    finalDelay: 5,
  });

  sequence.start();
  sequence.succeed();
  scheduler.runAll();

  assert.deepEqual(states.map((state) => state.index), [0, 1, 2, 3, 4, 5, 6, 7, 7]);
  assert.equal(states.at(-1).phase, "completed");
});


test("an early success response keeps delivery visible before decryption", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
    stepDelay: 10,
    finalDelay: 5,
  });

  sequence.start();
  sequence.succeed();
  for (let transition = 0; transition < 6; transition += 1) {
    scheduler.runNext();
  }

  assert.deepEqual(states.at(-1), { index: 6, phase: "waiting", message: "" });
  assert.equal(scheduler.count(), 1);
  scheduler.runNext();
  assert.equal(states.at(-1).phase, "decrypting");
});


test("failure stops progression and retains its message", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
    stepDelay: 10,
    finalDelay: 5,
  });

  sequence.start();
  scheduler.runNext();
  sequence.fail("Could not communicate with Bob.");

  assert.deepEqual(states.at(-1), {
    index: 1,
    phase: "failed",
    message: "Could not communicate with Bob.",
  });
  assert.equal(scheduler.count(), 0);
});


test("reset returns the sequence to ready", () => {
  const scheduler = createFakeScheduler();
  const states = [];
  const sequence = createProtocolSequence({
    onChange: (state) => states.push(state),
    schedule: scheduler.schedule,
    cancel: scheduler.cancel,
  });

  sequence.start();
  sequence.fail("Stopped");
  sequence.reset();

  assert.deepEqual(states.at(-1), { index: -1, phase: "ready", message: "" });
});


test("reduced motion uses shorter ordered status timing", () => {
  const regular = getSequenceTiming(false);
  const reduced = getSequenceTiming(true);

  assert.ok(reduced.stepDelay < regular.stepDelay);
  assert.ok(reduced.finalDelay < regular.finalDelay);
  assert.ok(reduced.stepDelay > 0);
  assert.ok(reduced.finalDelay > 0);
});
