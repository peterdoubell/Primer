/* Two views of one authored state; no persistence or cross-lesson messages. */
(function () {
  'use strict';
  const allowed = new Set(['math.5.complex-analysis', 'phys.4.quantum', 'math.5.topology', 'phys.4.relativity']);
  const views = new Map();
  function join(key, root, receive) {
    if (!allowed.has(key) || !root || typeof receive !== 'function' || typeof WeakRef !== 'function') return;
    root.receiveLessonState = receive;
    const refs = (views.get(key) || []).filter(ref => ref.deref());
    refs.push(new WeakRef(root));
    views.set(key, refs);
  }
  function publish(key, source, state) {
    if (!allowed.has(key) || !state || typeof state !== 'object') return;
    const refs = (views.get(key) || []).filter(ref => {
      const root = ref.deref();
      return root && root.isConnected !== false;
    });
    views.set(key, refs);
    for (const ref of refs) {
      const root = ref.deref();
      if (root !== source && typeof root.receiveLessonState === 'function') root.receiveLessonState({...state});
    }
  }
  const api = Object.freeze({join, publish});
  if (typeof window !== 'undefined') window.PrimerLessonStateBus = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
