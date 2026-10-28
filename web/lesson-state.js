/* Two views of one authored state; no persistence or cross-lesson messages. */
(function () {
  'use strict';
  const allowed = new Set(['math.3.linear', 'math.3.slope', 'math.3.quadratics', 'math.3.polynomials', 'math.5.complex-analysis', 'phys.4.quantum', 'math.5.topology', 'phys.4.relativity', 'math.5.abstract', 'phys.5.quantum-info', 'math.5.logic', 'phys.4.em-maxwell', 'phys.5.gr-cosmo', 'phys.5.qft', 'math.4.numtheory']);
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
