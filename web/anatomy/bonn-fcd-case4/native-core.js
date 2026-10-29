// Native NIfTI cell geometry and C-order plane decoding. No fitted registration.
export function planeGeometry(volume, axis) {
  if (!Number.isInteger(axis) || axis < 0 || axis > 2) throw Error('Invalid plane axis');
  const remaining = [0, 1, 2].filter(a => a !== axis);
  const [uAxis, vAxis] = remaining;
  const spacing = a => Math.hypot(...volume.affine.slice(0, 3).map(row => row[a]));
  const direction = (a, positive) => {
    const column = volume.affine.slice(0, 3).map(row => row[a]);
    const dominant = column.map(Math.abs).indexOf(Math.max(...column.map(Math.abs)));
    return [['L', 'R'], ['P', 'A'], ['I', 'S']][dominant][column[dominant] * (positive ? 1 : -1) > 0 ? 1 : 0];
  };
  return {uAxis, vAxis, width:volume.shape[uAxis], height:volume.shape[vAxis],
    spacingU:spacing(uAxis), spacingV:spacing(vAxis),
    edges:[direction(uAxis, false), direction(uAxis, true), direction(vAxis, true), direction(vAxis, false)]};
}

export function decodeStored(bytes, dtype) {
  const types = {'<i2':[2, 'getInt16', Int16Array], '<u2':[2, 'getUint16', Uint16Array],
    '|u1':[1, 'getUint8', Uint8Array], '<f4':[4, 'getFloat32', Float32Array]};
  const type = types[dtype];
  if (!type || bytes.byteLength % type[0]) throw Error('Unsupported or truncated source samples');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const result = new type[2](bytes.byteLength / type[0]);
  for (let i = 0; i < result.length; i++) {
    result[i] = view[type[1]](i * type[0], true);
    if (!Number.isFinite(result[i])) throw Error('Nonfinite source sample');
  }
  return result;
}

export function renderNative(values, volume, axis, low, high, labels = null, mode = 'mri') {
  if (!['mri', 'overlay', 'mask'].includes(mode)) throw Error('Invalid display mode');
  if (!Number.isFinite(low) || !Number.isFinite(high) || high <= low) throw Error('Invalid window');
  if (!Number.isFinite(volume.slope) || !Number.isFinite(volume.intercept)) throw Error('Invalid source scaling');
  const g = planeGeometry(volume, axis);
  if (values.length !== g.width * g.height || labels && labels.length !== values.length) throw Error('Plane size mismatch');
  if (mode !== 'mri' && !labels) throw Error('Annotation unavailable');
  const pixels = new Uint8ClampedArray(values.length * 4);
  for (let v = 0; v < g.height; v++) for (let u = 0; u < g.width; u++) {
    const source = u * g.height + v, target = ((g.height - 1 - v) * g.width + u) * 4;
    if (labels && labels[source] !== 0 && labels[source] !== 1) throw Error('Unexpected lesion label');
    const grey = Math.round(255 * Math.max(0, Math.min(1, (values[source] * volume.slope + volume.intercept - low) / (high - low))));
    const on = labels && labels[source] === 1;
    const rgb = mode === 'mask' ? (on ? [255, 100, 20] : [0, 0, 0]) :
      mode === 'overlay' && on ? [Math.round(.55 * grey + .45 * 255), Math.round(.55 * grey + .45 * 100), Math.round(.55 * grey + .45 * 20)] : [grey, grey, grey];
    pixels.set([...rgb, 255], target);
  }
  return {pixels, geometry:g};
}

export function pixelToVoxel(volume, axis, slice, x, y) {
  const g = planeGeometry(volume, axis);
  if (![slice, x, y].every(Number.isInteger) || slice < 0 || slice >= volume.shape[axis] || x < 0 || x >= g.width || y < 0 || y >= g.height) throw Error('Pixel outside source');
  const ijk = [0, 0, 0]; ijk[axis] = slice; ijk[g.uAxis] = x; ijk[g.vAxis] = g.height - 1 - y;
  return ijk;
}

export function voxelToWorld(volume, ijk) {
  return volume.affine.slice(0, 3).map(row => row[3] + ijk.reduce((sum, n, a) => sum + row[a] * n, 0));
}

export function annotationAllowed(role) { return role === 'flair'; }
