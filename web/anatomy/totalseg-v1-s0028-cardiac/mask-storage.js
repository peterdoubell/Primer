'use strict';
(function (root) {
  function pack(binary) {
    if (!(binary instanceof Uint8Array)) throw new TypeError('Original mask must be Uint8Array');
    const bits = new Uint8Array(Math.ceil(binary.length / 8));
    for (let i = 0; i < binary.length; i++) {
      if (binary[i] !== 0 && binary[i] !== 1) throw new RangeError('Original mask must contain only zero and one');
      if (binary[i]) bits[i >>> 3] |= 1 << (i & 7);
    }
    return bits;
  }
  const value = (bits, index) => (bits[index >>> 3] >>> (index & 7)) & 1;
  const api = Object.freeze({ pack, value });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.CardiacMaskStorage = api;
})(typeof window === 'undefined' ? globalThis : window);
