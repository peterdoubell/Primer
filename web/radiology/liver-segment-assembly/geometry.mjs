// Mesh vertices are stored in native axis millimetres. The source affine's
// translation is needed for patient coordinates, but does not change relative positions.
export function gridBounds(labels, shape, margin = 0) {
  return [0, 1].map((end) =>
    shape.map((size, axis) => {
      const values = labels.map((row) => row.boundsIndex[end][axis]);
      return end
        ? Math.min(size - 1, Math.max(...values) + margin)
        : Math.max(0, Math.min(...values) - margin);
    })
  );
}

export function patientPosition(affine, ijk) {
  return affine
    .slice(0, 3)
    .map((row) => row[3] + ijk.reduce((sum, value, axis) => sum + value * row[axis], 0));
}

export function sectionData(frame, bounds, labels, spacing, visible, display) {
  const { horizontal: h, vertical: v } = frame.axes;
  const width = bounds[1][h] - bounds[0][h] + 1,
    height = bounds[1][v] - bounds[0][v] + 1;
  const raster = new Uint8ClampedArray(width * height * 4);
  const texture = new Uint8Array(raster.length),
    counts = new Uint32Array(10);
  const colors = [null, ...labels.map((row) => row.color)];
  for (let y = 0; y < height; y++) {
    const srcV = bounds[0][v] + y;
    for (let x = 0; x < width; x++) {
      const srcH = bounds[0][h] + x;
      const index = (frame.height - 1 - srcV) * frame.width + srcH;
      const code = frame.labels[index],
        on = !!code && visible.has(code);
      if (code) counts[code]++;
      // Positive vertical and horizontal axes are reversed for the radiological screen view.
      const pixel = 4 * ((height - 1 - y) * width + width - 1 - x);
      const texel = 4 * (y * width + x);
      const grey = Math.max(0, Math.min(255, Math.round(((frame.image[index] + 125) * 255) / 350)));
      const edge =
        on &&
        (srcH === 0 ||
          srcH === frame.width - 1 ||
          srcV === 0 ||
          srcV === frame.height - 1 ||
          frame.labels[index - 1] !== code ||
          frame.labels[index + 1] !== code ||
          frame.labels[index - frame.width] !== code ||
          frame.labels[index + frame.width] !== code);
      let rgb;
      if (display === 'map') rgb = on ? colors[code] : [13, 20, 27];
      else rgb = display === 'outline' && edge ? colors[code] : [grey, grey, grey];
      raster.set(rgb, pixel);
      raster[pixel + 3] = 255;
      if (on) {
        texture.set(rgb, texel);
        texture[texel + 3] = 255;
      }
    }
  }
  return { width, height, raster, texture, counts, pixelArea: spacing[h] * spacing[v] };
}

// The texture spans cell edges. At native index n its centre is n * spacing.
export function sectionQuad(axes, bounds, spacing, fixed) {
  const { horizontal: h, vertical: v, normal: n } = axes;
  const vertices = [];
  for (const [u, t] of [
    [0, 0],
    [1, 0],
    [0, 1],
    [0, 1],
    [1, 0],
    [1, 1]
  ]) {
    const p = [0, 0, 0];
    p[n] = fixed * spacing[n];
    p[h] = (bounds[u][h] + (u ? 0.5 : -0.5)) * spacing[h];
    p[v] = (bounds[t][v] + (t ? 0.5 : -0.5)) * spacing[v];
    vertices.push(...p, u, t);
  }
  return new Float32Array(vertices);
}

// Components of the source R, A and S unit vectors projected on screen-right and screen-up.
export function referenceAxes(yaw, pitch) {
  return [
    ['R', -Math.cos(yaw), -Math.sin(pitch) * Math.sin(yaw)],
    ['A', Math.sin(yaw), -Math.sin(pitch) * Math.cos(yaw)],
    ['S', 0, Math.cos(pitch)]
  ];
}
