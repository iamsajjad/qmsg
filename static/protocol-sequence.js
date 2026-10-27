(function exposeProtocolSequence(globalScope, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (globalScope) {
    globalScope.QuantaProtocol = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildProtocolSequence() {
  const DELIVERY_INDEX = 6;
  const DECRYPTION_INDEX = 7;

  function getSequenceTiming(prefersReducedMotion) {
    return prefersReducedMotion
      ? { stepDelay: 80, finalDelay: 80 }
      : { stepDelay: 620, finalDelay: 360 };
  }

  function createProtocolSequence(options) {
    const onChange = options.onChange;
    const schedule = options.schedule || setTimeout;
    const cancel = options.cancel || clearTimeout;
    const stepDelay = options.stepDelay ?? 620;
    const finalDelay = options.finalDelay ?? 360;
    let timer = null;
    let successPending = false;
    let state = { index: -1, phase: "ready", message: "" };

    function emit() {
      onChange({ ...state });
    }

    function clearScheduledTransition() {
      if (timer !== null) {
        cancel(timer);
        timer = null;
      }
    }

    function beginDecryption() {
      successPending = false;
      state = { index: DECRYPTION_INDEX, phase: "decrypting", message: "" };
      emit();
      timer = schedule(() => {
        timer = null;
        state = { index: DECRYPTION_INDEX, phase: "completed", message: "" };
        emit();
      }, finalDelay);
    }

    function advance() {
      if (state.index >= DELIVERY_INDEX) {
        state = { index: DELIVERY_INDEX, phase: "waiting", message: "" };
        emit();
        return;
      }

      const nextIndex = state.index + 1;
      state = {
        index: nextIndex,
        phase: nextIndex === DELIVERY_INDEX ? "waiting" : "running",
        message: "",
      };
      emit();
      if (nextIndex < DELIVERY_INDEX) {
        timer = schedule(advance, stepDelay);
      } else if (successPending) {
        timer = schedule(beginDecryption, stepDelay);
      } else {
        timer = null;
      }
    }

    return {
      start() {
        clearScheduledTransition();
        successPending = false;
        state = { index: 0, phase: "running", message: "" };
        emit();
        timer = schedule(advance, stepDelay);
      },
      succeed() {
        if (state.phase === "running" && state.index < DELIVERY_INDEX) {
          successPending = true;
          return;
        }
        clearScheduledTransition();
        beginDecryption();
      },
      fail(message) {
        clearScheduledTransition();
        successPending = false;
        state = {
          index: Math.max(state.index, 0),
          phase: "failed",
          message: String(message || "Delivery failed."),
        };
        emit();
      },
      reset() {
        clearScheduledTransition();
        successPending = false;
        state = { index: -1, phase: "ready", message: "" };
        emit();
      },
    };
  }

  return { createProtocolSequence, getSequenceTiming };
});
