// Immutable public payloads never receive app credentials. Range bodies are
// verified directly because Blob does not expose Content-Range through CORS.
export const sha = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(n => n.toString(16).padStart(2, '0')).join('');
export async function verified(bytes, size, digest) {
  if (bytes.byteLength !== size || await sha(bytes) !== digest) throw Error('Source integrity check failed');
  return bytes;
}
export async function decode(bytes, size, digest) {
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  const reader = stream.getReader(), chunks = []; let total = 0;
  try {
    while (true) { const {value, done} = await reader.read(); if (done) break;
      total += value.length; if (total > size) throw Error('Decoded source exceeds declared length'); chunks.push(value); }
  } finally { await reader.cancel(); }
  const raw = new Uint8Array(total); let offset = 0;
  for (const chunk of chunks) { raw.set(chunk, offset); offset += chunk.length; }
  return verified(raw, size, digest);
}
export function payloadURL(prefix, file, digest) {
  if (prefix !== 'https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com/radiology-native/openear-zeta-1473724/runtime/' || !/^[a-zA-Z0-9.-]+$/.test(file) || !/^[a-f0-9]{64}$/.test(digest)) throw Error('Invalid source address');
  return prefix + digest + '/' + file;
}
export async function payload(prefix, file, identity, member, signal) {
  const url = payloadURL(prefix, file, identity.sha256);
  if (member && (!Number.isInteger(member.offset) || member.offset < 0 || member.gzipBytes <= 0 || member.offset + member.gzipBytes > identity.bytes)) throw Error('Invalid source range');
  const controller = new AbortController();
  let timedOut = false;
  const onAbort = () => controller.abort();
  signal?.addEventListener('abort', onAbort, {once:true});
  if (signal?.aborted) onAbort();
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 45000);
  try {
    const response = await fetch(url, {credentials:'omit', signal:controller.signal, headers:member ? {Range:`bytes=${member.offset}-${member.offset + member.gzipBytes - 1}`} : {}});
    if (response.status !== (member ? 206 : 200)) throw Error('Source transport returned HTTP ' + response.status);
    const size = member ? member.gzipBytes : identity.bytes;
    const reader = response.body.getReader(), chunks = []; let total = 0;
    try { while (true) { const {value,done} = await reader.read(); if (done) break;
      total += value.length; if (total > size) throw Error('Source response exceeds declared length'); chunks.push(value); }
    } finally { await reader.cancel(); }
    const bytes = new Uint8Array(total); let offset=0;
    for (const chunk of chunks) { bytes.set(chunk,offset);offset+=chunk.length; }
    await verified(bytes,size,member ? member.gzipSHA256 : identity.sha256);
    if (timedOut) throw Error('Source transfer timed out');
    if (signal?.aborted) throw new DOMException('Superseded request','AbortError');
    return bytes;
  } catch (error) {
    if (timedOut && !signal?.aborted) throw Error('Source transfer timed out');
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onAbort);
    controller.abort();
  }
}
