export function symmetries(n, allowFlip) {
  const maps = [];
  for (const reflected of allowFlip ? [false, true] : [false]) {
    for (let shift = 0; shift < n; shift++) {
      const image = Array.from({ length: n }, (_, i) => (shift + (reflected ? -i : i) + n) % n);
      const visited = new Set();
      const cycles = [];
      for (let i = 0; i < n; i++) {
        if (visited.has(i)) continue;
        const cycle = [];
        let position = i;
        while (!visited.has(position)) {
          visited.add(position);
          cycle.push(position);
          position = image[position];
        }
        cycles.push(cycle);
      }
      maps.push({ reflected, shift, image, cycles });
    }
  }
  return maps;
}

export function applyMap(pattern, map) {
  const result = Array(pattern.length);
  for (const [source, destination] of map.image.entries()) result[destination] = pattern[source];
  return result;
}

function fixedBeadPatterns(cycles, dark) {
  // Choose whole cycles for the dark beads. Descending order uses each cycle once.
  const ways = Array(dark + 1).fill(0);
  ways[0] = 1;
  for (const cycle of cycles) {
    for (let total = dark; total >= cycle.length; total--) ways[total] += ways[total - cycle.length];
  }
  return ways[dark];
}

export function analyse(pattern, guests, allowFlip) {
  const n = pattern.length;
  const maps = symmetries(n, allowFlip);
  const factorial = Array.from({ length: n }, (_, i) => i + 1).reduce((a, b) => a * b, 1);
  const dark = pattern.filter(value => value === 1).length;
  let fixedSum = 0;
  let stabilizer = 0;
  const arrangements = new Set();
  const results = maps.map(map => {
    const transformed = applyMap(pattern, map);
    const fixesExample = transformed.every((value, i) => value === pattern[i]);
    const fixedCount = guests
      ? (map.cycles.length === n ? factorial : 0)
      : fixedBeadPatterns(map.cycles, dark);
    fixedSum += fixedCount;
    if (fixesExample) stabilizer++;
    arrangements.add(transformed.join(','));
    return { ...map, transformed, fixedCount, fixesExample };
  });
  return {
    results, fixedSum, dark, stabilizer, orbitSize: arrangements.size,
    labelled: results[0].fixedCount, classes: fixedSum / maps.length,
  };
}
