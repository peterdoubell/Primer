export const planes = {
  ij: { horizontal: 0, vertical: 1, normal: 2, name: 'I–J', fixedName: 'K' },
  ik: { horizontal: 0, vertical: 2, normal: 1, name: 'I–K', fixedName: 'J' },
  jk: { horizontal: 1, vertical: 2, normal: 0, name: 'J–K', fixedName: 'I' },
};

export async function fingerprint(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  return Array.from(digest, value => value.toString(16).padStart(2, '0')).join('');
}

export function assetURL(file, base = import.meta.url) {
  if (typeof file !== 'string' || !file) throw Error('A source asset path is missing.');
  const directory = new URL('./', base);
  const target = new URL(file, directory);
  if (directory.origin !== new URL(import.meta.url).origin || target.origin !== directory.origin
      || !target.pathname.startsWith(directory.pathname)
      || target.search || target.hash) throw Error('Unexpected source asset path.');
  return target;
}

export async function verifiedBytes(record, signal, base = import.meta.url) {
  const response = await fetch(assetURL(record.file, base), { signal });
  if (!response.ok) throw Error('A source file could not be retrieved.');
  const packed = await response.arrayBuffer();
  signal?.throwIfAborted();
  if (packed.byteLength !== record.bytes || await fingerprint(packed) !== record.sha256) {
    throw Error('The compressed source checksum differs.');
  }
  const decoded = await new Response(new Blob([packed]).stream()
    .pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  signal?.throwIfAborted();
  if (await fingerprint(decoded) !== record.decodedSHA256) {
    throw Error('The decoded source checksum differs.');
  }
  return decoded;
}

export class FetchPool {
  constructor(limit = 3) {
    this.limit = limit;
    this.active = 0;
    this.queue = [];
    this.maximumActive = 0;
  }

  drain() {
    while (this.active < this.limit && this.queue.length) {
      const entry = this.queue.shift();
      if (entry.signal?.aborted) continue;
      entry.signal?.removeEventListener('abort', entry.abort);
      this.active += 1;
      this.maximumActive = Math.max(this.maximumActive, this.active);
      entry.resolve();
    }
  }

  async run(task, signal) {
    signal?.throwIfAborted();
    await new Promise((resolve, reject) => {
      const entry = { resolve, reject, signal };
      entry.abort = () => {
        reject(signal.reason);
        this.drain();
      };
      signal?.addEventListener('abort', entry.abort, { once: true });
      this.queue.push(entry);
      this.drain();
    });
    try {
      signal?.throwIfAborted();
      return await task();
    } finally {
      this.active -= 1;
      this.drain();
    }
  }
}

const shaPattern = /^[a-f0-9]{64}$/;
const integerVector = value => Array.isArray(value) && value.length === 3
  && value.every(component => Number.isSafeInteger(component));

export function validateCase(record) {
  if (typeof record.id !== 'string' || !integerVector(record.shape)
      || !record.shape.every(value => value > 0)
      || !Array.isArray(record.spacingMm) || record.spacingMm.length !== 3
      || !record.spacingMm.every(value => Number.isFinite(value) && value > 0)
      || !Number.isSafeInteger(record.brickSize) || record.brickSize < 1
      || !Array.isArray(record.bricks) || !Array.isArray(record.labels) || !record.labels.length) {
    throw Error('The source volume geometry is invalid.');
  }
  const lattice = new Map();
  for (const brick of record.bricks) {
    if (!integerVector(brick.start) || !integerVector(brick.size)
        || !brick.start.every((value, axis) => value >= 0 && value < record.shape[axis]
          && value % record.brickSize === 0)
        || !brick.size.every((value, axis) => value === Math.min(record.brickSize, record.shape[axis] - brick.start[axis]))
        || !Number.isSafeInteger(brick.bytes) || brick.bytes < 1
        || !shaPattern.test(brick.sha256) || !shaPattern.test(brick.decodedSHA256)) {
      throw Error('A source brick has invalid geometry or identity.');
    }
    const key = brick.start.join(',');
    if (lattice.has(key)) throw Error('The source inventory repeats a brick.');
    lattice.set(key, brick);
  }
  let expected = 0;
  for (let k = 0; k < record.shape[2]; k += record.brickSize) {
    for (let j = 0; j < record.shape[1]; j += record.brickSize) {
      for (let i = 0; i < record.shape[0]; i += record.brickSize) {
        if (!lattice.has([i, j, k].join(','))) throw Error('The source inventory has a missing brick.');
        expected += 1;
      }
    }
  }
  if (expected !== lattice.size) throw Error('The source brick count differs.');
  const codes = new Set();
  for (const label of record.labels) {
    if (!Number.isInteger(label.code) || label.code < 1 || label.code > 255 || codes.has(label.code)
        || typeof label.name !== 'string' || !Array.isArray(label.color) || label.color.length !== 3
        || !label.color.every(value => Number.isInteger(value) && value >= 0 && value <= 255)
        || !Number.isSafeInteger(label.voxelCount) || label.voxelCount < 0) {
      throw Error('A source label is invalid.');
    }
    if (label.voxelCount && (!integerVector(label.focus)
        || !label.focus.every((value, axis) => value >= 0 && value < record.shape[axis]))) {
      throw Error('A label focus is outside the source array.');
    }
    codes.add(label.code);
  }
  return record;
}

export function nativeReader(record, pool = new FetchPool(), read = verifiedBytes, cacheLimit = 12 * 1024 * 1024) {
  validateCase(record);
  const ct = record.encoding === 'int16-le+two-labels';
  if (record.encoding !== undefined && !ct) throw Error('Unrecognised source sample format.');
  const sampleBytes = ct ? 4 : 2;
  const cache = new Map();
  let usedBytes = 0;
  let maximumBytes = 0;

  async function brickBytes(brick, signal) {
    const cached = cache.get(brick.file);
    if (cached) {
      cache.delete(brick.file);
      cache.set(brick.file, cached);
      return cached;
    }
    return pool.run(async () => {
      const decoded = await read(brick, signal);
      const expected = brick.size.reduce((product, value) => product * value, sampleBytes);
      if (decoded.byteLength !== expected) throw Error('The image and label byte count differs.');
      signal?.throwIfAborted();
      // Another section may have verified the same brick while this fetch ran.
      const existing = cache.get(brick.file);
      if (existing) return existing;
      const view = new Uint8Array(decoded);
      while (cache.size && usedBytes + view.byteLength > cacheLimit) {
        const oldest = cache.keys().next().value;
        usedBytes -= cache.get(oldest).byteLength;
        cache.delete(oldest);
      }
      if (view.byteLength <= cacheLimit) {
        cache.set(brick.file, view);
        usedBytes += view.byteLength;
        maximumBytes = Math.max(maximumBytes, usedBytes);
      }
      return view;
    }, signal);
  }

  async function section(planeKey, position, signal) {
    const axes = planes[planeKey];
    if (!axes || !integerVector(position)
        || !position.every((value, axis) => value >= 0 && value < record.shape[axis])) {
      throw Error('The requested source section is outside the array.');
    }
    const width = record.shape[axes.horizontal];
    const height = record.shape[axes.vertical];
    const fixed = position[axes.normal];
    const image = ct ? new Int16Array(width * height) : new Uint8Array(width * height);
    const overlap = ct ? new Uint8Array(width * height) : null;
    const labels = new Uint8Array(width * height);
    const bricks = record.bricks.filter(brick => fixed >= brick.start[axes.normal]
      && fixed < brick.start[axes.normal] + brick.size[axes.normal]);
    let cursor = 0;
    let written = 0;

    async function worker() {
      while (cursor < bricks.length) {
        signal?.throwIfAborted();
        const brick = bricks[cursor++];
        const bytes = await brickBytes(brick, signal);
        signal?.throwIfAborted();
        const strides = [1, brick.size[0], brick.size[0] * brick.size[1]];
        const h0 = brick.start[axes.horizontal], v0 = brick.start[axes.vertical];
        const normalOffset = (fixed - brick.start[axes.normal]) * strides[axes.normal];
        for (let v = 0; v < brick.size[axes.vertical]; v += 1) {
          const row = height - 1 - (v0 + v);
          const start = normalOffset + v * strides[axes.vertical];
          for (let h = 0; h < brick.size[axes.horizontal]; h += 1) {
            const input = sampleBytes * (start + h * strides[axes.horizontal]);
            const output = row * width + h0 + h;
            if (ct) {
              image[output] = bytes[input] | (bytes[input + 1] << 8);
              labels[output] = bytes[input + 2];
              overlap[output] = bytes[input + 3];
            } else {
              image[output] = bytes[input];
              labels[output] = bytes[input + 1];
            }
            written += 1;
          }
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(3, bricks.length) }, worker));
    signal?.throwIfAborted();
    if (written !== width * height) throw Error('The source section is incomplete.');
    return { image, labels, ...(overlap ? { overlap } : {}), width, height, axes, fixed, position: [...position],
      spacing: [record.spacingMm[axes.horizontal], record.spacingMm[axes.vertical]] };
  }

  return { section, stats: () => ({ cacheBytes: usedBytes, maximumBytes, cacheLimit, cachedBricks: cache.size,
    maximumConcurrentFetches: pool.maximumActive }) };
}
