export const traits = {
  body_mass_g: { name: 'Body mass', unit: 'g', bin: 250 },
  bill_length_mm: { name: 'Bill length', unit: 'mm', bin: 2 },
  bill_depth_mm: { name: 'Bill depth', unit: 'mm', bin: 1 },
  flipper_length_mm: { name: 'Flipper length', unit: 'mm', bin: 5 }
};

export const species = ['Adelie', 'Chinstrap', 'Gentoo'];
export const displayName = (value) => (value === 'Adelie' ? 'Adélie' : value);

// The pinned CSV has no quoted fields. Preserve the row number and the source NA cells.
export function readObservations(csv) {
  const [first, ...lines] = csv.trimEnd().split(/\r?\n/);
  const fields = first.split(',');
  if (
    fields.join(',') !==
    'species,island,bill_length_mm,bill_depth_mm,flipper_length_mm,body_mass_g,sex,year'
  ) {
    throw Error('Unexpected field-study header.');
  }
  return lines.map((line, i) => {
    const values = line.split(',');
    if (values.length !== fields.length || !species.includes(values[0]))
      throw Error('Unexpected field-study row.');
    const observation = { row: i + 1 };
    fields.forEach((key, col) => {
      const raw = values[col];
      if (raw === 'NA') observation[key] = null;
      else if (key in traits) {
        const n = Number(raw);
        if (!raw || !Number.isFinite(n) || n <= 0) throw Error('Invalid source measurement.');
        observation[key] = n;
      } else observation[key] = raw;
    });
    return observation;
  });
}

export function summary(rows, key) {
  const values = rows
    .map((row) => row[key])
    .filter(Number.isFinite)
    .sort((a, b) => a - b);
  const n = values.length;
  if (!n) return null;
  const quantile = (p) => {
    const position = (n - 1) * p,
      low = Math.floor(position);
    return values[low] + (position - low) * (values[Math.ceil(position)] - values[low]);
  };
  const mean = values.reduce((sum, x) => sum + x, 0) / n;
  return {
    n,
    min: values[0],
    max: values[n - 1],
    mean,
    median: quantile(0.5),
    q1: quantile(0.25),
    q3: quantile(0.75),
    sd: n > 1 ? Math.sqrt(values.reduce((sum, x) => sum + (x - mean) ** 2, 0) / (n - 1)) : null
  };
}

export function fit(rows, x, y) {
  const points = rows.filter((row) => Number.isFinite(row[x]) && Number.isFinite(row[y]));
  if (points.length < 2) return null;
  const sum = (fn) => points.reduce((total, row) => total + fn(row), 0);
  const mx = sum((row) => row[x]) / points.length,
    my = sum((row) => row[y]) / points.length;
  const xx = sum((row) => (row[x] - mx) ** 2),
    yy = sum((row) => (row[y] - my) ** 2);
  if (!xx) return null;
  const xy = sum((row) => (row[x] - mx) * (row[y] - my));
  const slope = xy / xx;
  return {
    n: points.length,
    slope,
    intercept: my - slope * mx,
    r: yy ? xy / Math.sqrt(xx * yy) : null,
    min: Math.min(...points.map((row) => row[x])),
    max: Math.max(...points.map((row) => row[x]))
  };
}

export function domain(rows, key) {
  const s = summary(rows, key),
    step = traits[key].bin;
  return [Math.floor(s.min / step) * step, (Math.floor(s.max / step) + 1) * step];
}

export function bins(rows, key, [min, max]) {
  const step = traits[key].bin;
  const groups = Array.from({ length: Math.round((max - min) / step) }, (_, i) => ({
    start: min + i * step,
    end: min + (i + 1) * step,
    counts: [0, 0, 0],
    total: 0
  }));
  rows.forEach((row) => {
    if (!Number.isFinite(row[key])) return;
    const group = groups[Math.floor((row[key] - min) / step)];
    group.counts[species.indexOf(row.species)]++;
    group.total++;
  });
  return groups;
}

export function project([x, y, z], yaw, pitch) {
  const a = (yaw * Math.PI) / 180,
    b = (pitch * Math.PI) / 180;
  const depth = x * Math.sin(a) + z * Math.cos(a);
  return {
    x: x * Math.cos(a) - z * Math.sin(a),
    y: y * Math.cos(b) - depth * Math.sin(b),
    depth: y * Math.sin(b) + depth * Math.cos(b)
  };
}
