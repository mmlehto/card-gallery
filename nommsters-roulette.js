(() => {
  // Inject tiny CSS so you don't have to touch your <style> block.
  const css = `
  .nommsters-roulette-pop { animation: nommstersRoulettePop 110ms ease-out; }
  @keyframes nommstersRoulettePop {
    from { transform: scale(.965); filter: blur(.6px); }
    to   { transform: scale(1);    filter: blur(0); }
  }`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  function randIndex(n) {
    return Math.floor(Math.random() * n);
  }

  /**
   * Runs a "fast -> slow" picker.
   * Returns a cancel() function.
   */
  function runRoulette({
    pool,
    onTick,
    onDone,
    onProgress,
    durationMs = 2600,
    startInterval = 45,
    endInterval = 320,
  }) {
    if (!Array.isArray(pool) || pool.length === 0) {
      throw new Error("runRoulette: pool must be a non-empty array");
    }

    const start = performance.now();
    let cancelled = false;
    let timeoutId = null;
    let lastCard = pool[randIndex(pool.length)];

    const step = () => {
      if (cancelled) return;

      const now = performance.now();
      const t = Math.min(1, (now - start) / durationMs);

      // Ease-out (slows down near the end)
      const ease = 1 - Math.pow(1 - t, 3);
      const interval = startInterval + (endInterval - startInterval) * ease;

      lastCard = pool[randIndex(pool.length)];
      onTick?.(lastCard);
      onProgress?.(t * 100);

      if (t >= 1) {
        onDone?.(lastCard);
        return;
      }

      timeoutId = setTimeout(step, interval);
    };

    step();

    return function cancel() {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }

  window.NommstersRoulette = { runRoulette };
})();
