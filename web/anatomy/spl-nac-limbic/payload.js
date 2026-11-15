'use strict';
(function (root) {
  const sha = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), value => value.toString(16).padStart(2, '0')).join('');

  async function decode(row, bytes) {
    if (!Number.isSafeInteger(row.byteLength) || row.byteLength <= 0 ||
        !/^[a-f0-9]{64}$/.test(row.gzipSHA256) || !/^[a-f0-9]{64}$/.test(row.decodedSHA256)) {
      throw Error('Source descriptor is invalid');
    }
    const receivedSHA256 = await sha(bytes);
    let decoded;
    if (receivedSHA256 === row.gzipSHA256) {
      // Hosts can send the original gzip file or decode it at HTTP level.
      // Only byte identity decides which representation was received.
      decoded = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    } else if (receivedSHA256 === row.decodedSHA256) {
      decoded = bytes;
    } else {
      throw Error('Source payload identity differs');
    }
    if (decoded.byteLength !== row.byteLength || await sha(decoded) !== row.decodedSHA256) {
      throw Error('Decoded source identity or length differs');
    }
    return decoded;
  }

  async function fetchPayload(row) {
    const response = await fetch(row.file);
    if (!response.ok) throw Error('Source request failed: ' + response.status);
    return decode(row, await response.arrayBuffer());
  }

  const api = Object.freeze({decode, fetchPayload});
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SPLSourcePayload = api;
})(globalThis);
