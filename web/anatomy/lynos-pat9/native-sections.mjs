const orientations = {
  axial: { normal: 2, horizontal: 0, vertical: 1, directions: ['A', 'P', 'R', 'L'] },
  coronal: { normal: 1, horizontal: 0, vertical: 2, directions: ['S', 'I', 'R', 'L'] },
  sagittal: { normal: 0, horizontal: 1, vertical: 2, directions: ['S', 'I', 'P', 'A'] },
};
const formats = {
  '<i2': { bytes: 2, read: 'getInt16', ArrayType: Int16Array },
  '<u2': { bytes: 2, read: 'getUint16', ArrayType: Uint16Array },
  '|u1': { bytes: 1, read: 'getUint8', ArrayType: Uint8Array },
};

async function hash(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  return Array.from(digest, byte => byte.toString(16).padStart(2, '0')).join('');
}

async function fetchPackedAsset(name, signal) {
  const response = await fetch(new URL(name, import.meta.url), { signal });
  if (!response.ok) throw Error('Source asset is unavailable.');
  return response.arrayBuffer();
}

export function nativeSectionReader(source, readPacked = fetchPackedAsset) {
  if (source.nativeIndexAxes.join(',') !== 'left,anterior,superior') {
    throw Error('Unexpected source index directions.');
  }
  const shape = source.shapeSliceRowColumn.toReversed();
  const strides = [1, shape[0], shape[0] * shape[1]];
  const cache = new Map();

  function dimensions(plane) {
    const { normal, horizontal, vertical, directions } = orientations[plane];
    return {
      width: shape[horizontal],
      height: shape[vertical],
      sections: shape[normal],
      spacingMm: [source.spacingXYZMm[horizontal], source.spacingXYZMm[vertical]],
      directions,
    };
  }

  async function loadChunk(row, format, signal) {
    if (cache.has(row.file)) {
      const loaded = cache.get(row.file);
      cache.delete(row.file);
      cache.set(row.file, loaded);
      return loaded;
    }
    if (!/^[a-z0-9-]+\.gz$/.test(row.file)) throw Error('Unexpected source asset name.');
    const packed = await readPacked(row.file, signal);
    signal?.throwIfAborted();
    if (packed.byteLength !== row.bytes || await hash(packed) !== row.compressedSHA256) {
      throw Error('Compressed source checksum differs.');
    }
    const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'));
    const decoded = await new Response(stream).arrayBuffer();
    signal?.throwIfAborted();
    const sampleCount = (row.sourceZStopExclusive - row.sourceZStart) * strides[2];
    if (decoded.byteLength !== sampleCount * format.bytes || decoded.byteLength !== row.decodedBytes
        || await hash(decoded) !== row.decodedSHA256) {
      throw Error('Decoded source checksum differs.');
    }
    signal?.throwIfAborted();
    const view = new DataView(decoded);
    cache.set(row.file, view);
    if (cache.size > 3) cache.delete(cache.keys().next().value);
    return view;
  }

  async function section(role, plane, fixed, signal) {
    const { normal, horizontal, vertical } = orientations[plane];
    const { width, height, sections, ...geometry } = dimensions(plane);
    const volume = source.volumes[role];
    const format = formats[volume.dtype];
    if (!Number.isInteger(fixed) || fixed < 0 || fixed >= sections) {
      throw RangeError('Section is outside the acquired volume.');
    }
    const pixels = new format.ArrayType(width * height);
    const chunks = normal === 2
      ? volume.chunks.filter(chunk => fixed >= chunk.sourceZStart && fixed < chunk.sourceZStopExclusive)
      : volume.chunks;
    let written = 0;
    for (const row of chunks) {
      signal?.throwIfAborted();
      const bytes = await loadChunk(row, format, signal);
      if (normal === 2) {
        const offset = (fixed - row.sourceZStart) * strides[2] * format.bytes;
        const rawPlane = new Uint8Array(bytes.buffer, offset, strides[2] * format.bytes);
        const expected = row.planes[fixed - row.sourceZStart];
        if (expected.sourceZIndex !== fixed || await hash(rawPlane) !== expected.decodedSHA256) {
          throw Error('Axial source section checksum differs.');
        }
      }
      const startY = normal === 2 ? 0 : height - row.sourceZStopExclusive;
      const stopY = normal === 2 ? height : height - row.sourceZStart;
      const planeOffset = fixed * strides[normal] - row.sourceZStart * strides[2];
      for (let y = startY; y < stopY; y += 1) {
        const start = planeOffset + (height - 1 - y) * strides[vertical];
        for (let x = 0; x < width; x += 1) {
          const index = start + x * strides[horizontal];
          pixels[y * width + x] = bytes[format.read](index * format.bytes, true);
          written += 1;
        }
      }
    }
    if (written !== pixels.length) throw Error('Source section is incomplete.');
    return { width, height, ...geometry, pixels };
  }

  return { dimensions, section };
}
