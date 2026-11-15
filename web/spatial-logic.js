/* Exact membership tables and directed dependency graphs; categorical layout has no metric. */
(function () {
  'use strict';
  const family = {
    title: 'Logical witnesses and proof dependencies', requires: 'PrimerMathLogicLab', linkedStateKey: 'math.5.logic',
    initialFactory: () => JSON.parse(JSON.stringify(window.PrimerMathLogicLab.initial)),
    normalize: raw => window.PrimerMathLogicLab.normalize(raw),
    controlsFactory: () => window.PrimerMathLogicLab.controls.map(c => ({...c, numericInput: !c.options,
      visibleWhen: c.stations ? {station: c.stations} : undefined})),
    build(state, g) {
      const m = window.PrimerMathLogicLab.build(state), panels = [];
      for (const [index, p] of m.panels.entries()) {
        const origin = [0, 0, index * 8];
        if (p.kind === 'table') {
          const values = [...new Set(p.cells.flat().map(v => String(v)))], n = p.cells.length, columns = p.columnLabels.length;
          const rowGain = 4 / Math.max(1, n - 1), columnGain = 4 / Math.max(1, columns - 1), valueGain = 2 / Math.max(1, values.length - 1);
          const cells = [];
          for (const [i, row] of p.cells.entries()) for (const [j, value] of row.entries()) {
            const ordinal = values.indexOf(String(value)), point = [i * rowGain, j * columnGain, origin[2] + ordinal * valueGain];
            g.sphere(point, .05, value === false ? g.colors.coral : g.colors.blue, {fidelity_kind: 'logic_cell', row: i, column: j, value, panel: index});
            cells.push({row: i, column: j, value, valueOrdinal: ordinal, point});
          }
          g.line([origin, [4, 0, origin[2]]], g.colors.ink, {fidelity_kind: 'categorical_axis'});
          g.line([origin, [0, 4, origin[2]]], g.colors.ink, {fidelity_kind: 'categorical_axis'});
          g.line([origin, [0, 0, origin[2] + 2]], g.colors.ink, {fidelity_kind: 'categorical_axis'});
          g.label([4.4, 0, origin[2]], 'Row'); g.label([0, 4.4, origin[2]], 'Column'); g.label([0, 0, origin[2] + 2.4], 'Value slot');
          panels.push({kind: p.kind, source: p, index, origin, cells, values, rowGain, columnGain, valueGain});
        } else {
          const xMin = Math.min(...p.nodes.map(n => n.x)), xMax = Math.max(...p.nodes.map(n => n.x)), yMin = Math.min(...p.nodes.map(n => n.y)), yMax = Math.max(...p.nodes.map(n => n.y));
          const xGain = 4 / Math.max(1, xMax - xMin), yGain = 4 / Math.max(1, yMax - yMin);
          const nodes = p.nodes.map((n, i) => ({...n, displayedLabel: String(i + 1), point: [(n.x - xMin) * xGain, (n.y - yMin) * yGain, origin[2]]}));
          const points = new Map(nodes.map(n => [n.id, n.point])), edges = [];
          for (const edge of p.edges) {
            const a = points.get(edge.from), b = points.get(edge.to);
            if (!a || !b) throw new Error('Logic dependency has an absent endpoint');
            let path;
            if (edge.from === edge.to) path = Array.from({length: 33}, (_, i) => { const t = Math.PI * .15 + i * Math.PI * 1.7 / 32; return [a[0] + .3 * Math.cos(t), a[1] + .35 + .3 * Math.sin(t), a[2]]; });
            else path = [a, b];
            g.line(path, g.colors.teal, {fidelity_kind: 'logic_edge', from: edge.from, to: edge.to, label: edge.label, panel: index});
            const tip = path[path.length - 1], previous = path[path.length - 2], dx = tip[0] - previous[0], dy = tip[1] - previous[1], length = Math.hypot(dx, dy);
            if (length > 0) g.line([[tip[0] - .12 * dx / length + .06 * dy / length, tip[1] - .12 * dy / length - .06 * dx / length, tip[2]], tip, [tip[0] - .12 * dx / length - .06 * dy / length, tip[1] - .12 * dy / length + .06 * dx / length, tip[2]]], g.colors.teal, {fidelity_kind: 'logic_arrow', from: edge.from, to: edge.to, panel: index});
            edges.push({...edge, path});
          }
          for (const n of nodes) { g.sphere(n.point, .065, g.colors.gold, {fidelity_kind: 'logic_node', id: n.id, panel: index}); g.label([n.point[0], n.point[1] + .2, n.point[2]], n.displayedLabel); }
          panels.push({kind: p.kind, source: p, index, origin, nodes, edges, xMin, yMin, xGain, yGain});
        }
      }
      const key = panels.map(p => p.kind === 'table' ? 'Table ' + (p.index + 1) + ': row labels ' + p.source.rowLabels.join(', ') + '; column labels ' + p.source.columnLabels.join(', ') + '; value slots ' + p.values.map((v, i) => i + '=' + v).join(', ') + '.' : 'Graph ' + (p.index + 1) + ': ' + p.nodes.map(n => n.displayedLabel + '=' + n.label).join('; ') + '.').join(' ');
      return {state: m.state, readout: m.readout + ' ' + key, note: m.boundary + ' This is a categorical arrangement of the exact same table entries and directed edges. Spacing, height and separate panel planes do not measure cardinality, ordinal magnitude, proof strength or physical depth. Only finite witnesses are computed; all infinite conclusions retain the theorem hypotheses in the companion activity.',
        legend: [{label: 'Exact table value', color: g.colors.blue}, {label: 'Directed logical relation', color: g.colors.teal}, {label: 'Named statement or element', color: g.colors.gold}],
        logic: {state: m.state, data: m.data, panels, proof: m.proof, boundary: m.boundary}};
    }
  };
  if (typeof window !== 'undefined') window.PrimerLogicSpatialFamily = family;
  if (typeof module !== 'undefined' && module.exports) module.exports = family;
}());
