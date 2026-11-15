/* Shared reader speech chunking. Imported directly by the numerical fidelity checks. */
(function () {
  'use strict';
  const SPEAK_CHUNK = 1200;
function splitForSpeech(text) {
  const clean = String(text == null ? '' : text).replace(/\s+/g, ' ').trim();
  if (!clean) return [];
  if (clean.length <= SPEAK_CHUNK) return [clean];
  // A decimal point or a dot inside a source URL is not a sentence boundary.
  // Require whitespace/end after punctuation, preserving numeric tokens intact.
  const sentences = clean.match(/[\s\S]+?(?:[.!?\u2026]+["\')\]]*(?=\s|$)|$)/g) || [clean];
  const out = [];
  let buf = '';
  for (const s of sentences) {
    let piece = s.trim();
    // One "sentence" longer than a whole chunk — a run-on caption, a list of
    // dates with no full stop in it. Fall back to word boundaries rather than
    // cutting a word in half.
    while (piece.length > SPEAK_CHUNK) {
      let cut = piece.lastIndexOf(' ', SPEAK_CHUNK);
      if (cut < SPEAK_CHUNK * 0.5) cut = SPEAK_CHUNK;
      if (buf) { out.push(buf); buf = ''; }
      out.push(piece.slice(0, cut).trim());
      piece = piece.slice(cut).trim();
    }
    if (!piece) continue;
    if (buf && buf.length + 1 + piece.length > SPEAK_CHUNK) { out.push(buf); buf = piece; }
    else buf = buf ? buf + ' ' + piece : piece;
  }
  if (buf) out.push(buf);
  return out;
}

  const api = Object.freeze({ splitForSpeech, SPEAK_CHUNK });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else globalThis.PrimerSpeechChunks = api;
})();
