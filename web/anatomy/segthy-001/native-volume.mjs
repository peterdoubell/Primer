export const planes = {
  ij: { horizontal: 0, vertical: 1, normal: 2, name: 'I–J', fixedName: 'K' },
  ik: { horizontal: 0, vertical: 2, normal: 1, name: 'I–K', fixedName: 'J' },
  jk: { horizontal: 1, vertical: 2, normal: 0, name: 'J–K', fixedName: 'I' },
};

export async function fingerprint(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  return Array.from(digest, value => value.toString(16).padStart(2, '0')).join('');
}

// These finite names are application-owned inventories, never request metadata.
// Node source verifiers use explicit offline readers; this HTTP adapter is browser-only.
const assetNames = new Map();
const httpScopes = new Map();
const sourceModule = new URL(import.meta.url);
const browserModule = ['https:', 'http:'].includes(sourceModule.protocol)
  && sourceModule.pathname === '/app/anatomy/segthy-001/native-volume.mjs'
  && !sourceModule.search && !sourceModule.hash;

function declareAssets(study, grids, meshes, modules) {
  const names = [...meshes];
  for (const [prefix, columns, rows, slices] of grids) {
    for (const i of columns) for (const j of rows) for (const k of slices) {
      names.push(`${prefix}${i}-${j}-${k}.gz`);
    }
  }
  const canonical = new Map(names.map(name => [name, name]));
  assetNames.set(study, canonical);
  if (!browserModule) return;
  const resources = new Map();
  for (const name of canonical.values()) {
    resources.set(name, Object.freeze({
      app: new URL(`/app/anatomy/${study}/${name}`, sourceModule).href,
      published: new URL(`/source-media/anatomy/${study}/${name}`, sourceModule).href,
    }));
  }
  for (const module of modules) {
    httpScopes.set(new URL(`/app/anatomy/${study}/${module}`, sourceModule).href, resources);
  }
}

declareAssets('segthy-001', [
  ["left-", [0, 96, 192, 288, 384, 480], [0, 96, 192, 288, 384], [0, 96, 192, 288]],
  ["right-", [0, 96, 192, 288, 384, 480], [0, 96, 192, 288, 384], [0, 96, 192, 288, 384]],
], ["left-1-mesh.gz", "left-2-mesh.gz", "left-3-mesh.gz", "right-1-mesh.gz", "right-4-mesh.gz", "right-5-mesh.gz"], ['native-volume.mjs', 'viewer.js', 'mesh-view.mjs']);
declareAssets('ct-torso-s0028', [
  ['brick-', [0, 64, 128, 192, 256], [0, 64, 128, 192, 256], [0, 64, 128, 192, 256, 320, 384]],
], ["lung-upper-lobe-left.mesh.gz", "lung-lower-lobe-left.mesh.gz", "lung-upper-lobe-right.mesh.gz", "lung-middle-lobe-right.mesh.gz", "lung-lower-lobe-right.mesh.gz", "esophagus.mesh.gz", "trachea.mesh.gz", "thyroid-gland.mesh.gz", "heart.mesh.gz", "atrial-appendage-left.mesh.gz", "spleen.mesh.gz", "kidney-right.mesh.gz", "kidney-left.mesh.gz", "gallbladder.mesh.gz", "liver.mesh.gz", "stomach.mesh.gz", "pancreas.mesh.gz", "adrenal-gland-right.mesh.gz", "adrenal-gland-left.mesh.gz", "small-bowel.mesh.gz", "duodenum.mesh.gz", "colon.mesh.gz", "urinary-bladder.mesh.gz", "kidney-cyst-left.mesh.gz", "aorta.mesh.gz", "pulmonary-vein.mesh.gz", "brachiocephalic-trunk.mesh.gz", "subclavian-artery-right.mesh.gz", "subclavian-artery-left.mesh.gz", "common-carotid-artery-right.mesh.gz", "common-carotid-artery-left.mesh.gz", "brachiocephalic-vein-left.mesh.gz", "brachiocephalic-vein-right.mesh.gz", "superior-vena-cava.mesh.gz", "inferior-vena-cava.mesh.gz", "portal-vein-and-splenic-vein.mesh.gz", "iliac-artery-left.mesh.gz", "iliac-artery-right.mesh.gz", "iliac-vena-left.mesh.gz", "iliac-vena-right.mesh.gz", "sacrum.mesh.gz", "spinal-cord.mesh.gz", "vertebrae-c5.mesh.gz", "vertebrae-c6.mesh.gz", "vertebrae-c7.mesh.gz", "vertebrae-t1.mesh.gz", "vertebrae-t2.mesh.gz", "vertebrae-t3.mesh.gz", "vertebrae-t4.mesh.gz", "vertebrae-t5.mesh.gz", "vertebrae-t6.mesh.gz", "vertebrae-t7.mesh.gz", "vertebrae-t8.mesh.gz", "vertebrae-t9.mesh.gz", "vertebrae-t10.mesh.gz", "vertebrae-t11.mesh.gz", "vertebrae-t12.mesh.gz", "vertebrae-l1.mesh.gz", "vertebrae-l2.mesh.gz", "vertebrae-l3.mesh.gz", "vertebrae-l4.mesh.gz", "vertebrae-l5.mesh.gz", "sternum.mesh.gz", "costal-cartilages.mesh.gz", "rib-left-1.mesh.gz", "rib-left-2.mesh.gz", "rib-left-3.mesh.gz", "rib-left-4.mesh.gz", "rib-left-5.mesh.gz", "rib-left-6.mesh.gz", "rib-left-7.mesh.gz", "rib-left-8.mesh.gz", "rib-left-9.mesh.gz", "rib-left-10.mesh.gz", "rib-left-11.mesh.gz", "rib-left-12.mesh.gz", "rib-right-1.mesh.gz", "rib-right-2.mesh.gz", "rib-right-3.mesh.gz", "rib-right-4.mesh.gz", "rib-right-5.mesh.gz", "rib-right-6.mesh.gz", "rib-right-7.mesh.gz", "rib-right-8.mesh.gz", "rib-right-9.mesh.gz", "rib-right-10.mesh.gz", "rib-right-11.mesh.gz", "rib-right-12.mesh.gz", "skull.mesh.gz", "humerus-left.mesh.gz", "humerus-right.mesh.gz", "scapula-left.mesh.gz", "scapula-right.mesh.gz", "clavicula-left.mesh.gz", "clavicula-right.mesh.gz", "femur-left.mesh.gz", "femur-right.mesh.gz", "hip-left.mesh.gz", "hip-right.mesh.gz", "gluteus-maximus-left.mesh.gz", "gluteus-maximus-right.mesh.gz", "gluteus-medius-left.mesh.gz", "gluteus-medius-right.mesh.gz", "gluteus-minimus-left.mesh.gz", "gluteus-minimus-right.mesh.gz", "autochthon-left.mesh.gz", "autochthon-right.mesh.gz", "iliopsoas-left.mesh.gz", "iliopsoas-right.mesh.gz"], ['viewer.js']);
const medsegAxis = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 480];
declareAssets('medseg-liver-001', [
  ['brick-', medsegAxis, medsegAxis, [0, 32]],
], ['segment-1.mesh.gz', 'segment-2.mesh.gz', 'segment-3.mesh.gz', 'segment-4a.mesh.gz', 'segment-4b.mesh.gz',
  'segment-5.mesh.gz', 'segment-6.mesh.gz', 'segment-7.mesh.gz', 'segment-8.mesh.gz'], ['viewer.js']);

export function sourceAssetName(study, file) {
  const name = assetNames.get(study)?.get(file);
  if (typeof file !== 'string' || !name) throw Error('Unknown source asset name.');
  return name;
}

function sourceResource(file, base) {
  const key = base instanceof URL ? base.href : base;
  const asset = httpScopes.get(key)?.get(file);
  if (typeof file !== 'string' || !asset) throw Error('Unknown browser source asset namespace or name.');
  return asset;
}

export function assetURL(file, base = import.meta.url) {
  // Return a copy so callers cannot alter the private, app-owned request table.
  return new URL(sourceResource(file, base).app);
}

export async function verifiedBytes(record, signal, base = import.meta.url) {
  const asset = sourceResource(record.file, base);
  // A hosted app route redirects to its published static counterpart. Never use
  // a response's Location value: both possible destinations come from the table.
  let response = await fetch(asset.app, { signal, mode: 'same-origin', credentials: 'same-origin', redirect: 'manual' });
  if (response.type === 'opaqueredirect' || [301, 302, 303, 307, 308].includes(response.status)) {
    response = await fetch(asset.published, { signal, mode: 'same-origin', credentials: 'same-origin', redirect: 'error' });
  }
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
