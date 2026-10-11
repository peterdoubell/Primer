/* Operation relations and exact map coordinates; categorical axes carry no metric. */
(function () {
  'use strict';
  const line = (g, points, color, kind, extra = {}) => {
    if (points.length > 1) g.line(points, color, {width: 1.5, fidelity_kind: kind, ...extra});
  };
  const key = value => JSON.stringify(value);
  const family = {
    title: 'Exact algebraic operations and maps', requires: 'PrimerMathAlgebraLab', linkedStateKey: 'math.5.abstract',
    initialFactory: () => ({...window.PrimerMathAlgebraLab.initial}),
    normalize: raw => window.PrimerMathAlgebraLab.normalize(raw),
    controlsFactory: () => window.PrimerMathAlgebraLab.controls.map(c => ({...c, numericInput: !c.options,
      preserveExact: !c.options, visibleWhen: c.stations ? {station: c.stations} : undefined})),
    build(state, g) {
      const a = window.PrimerMathAlgebraLab, m = a.build(state), panels = [], primitives = [];
      m.panels.forEach((p, index) => {
        const origin = [0, 0, index * 7], record = {index, kind: p.kind, origin, source: p};
        if (p.kind === 'table') {
          const n = p.table.length, columns = Math.max(...p.table.map(row => row.length));
          const values = [...new Map(p.table.flat().map(v => [key(v), v])).values()];
          const outputIndex = v => values.findIndex(value => key(value) === key(v));
          const rowGain = 4 / Math.max(1, n - 1), columnGain = 4 / Math.max(1, columns - 1);
          const outputGain = 3 / Math.max(1, values.length - 1), cells = [];
          p.table.forEach((row, i) => row.forEach((value, j) => {
            const ordinal = outputIndex(value), point = [i * rowGain, j * columnGain, origin[2] + ordinal * outputGain];
            const selected = p.selected?.[0] === i && p.selected?.[1] === j;
            g.sphere(point, selected ? .065 : .026, selected ? g.colors.coral : g.colors.blue,
              {fidelity_kind: 'operation_cell', row: i, column: j, value, outputOrdinal: ordinal});
            cells.push({row: i, column: j, value, outputOrdinal: ordinal, point, selected});
          }));
          for (const [end, text] of [[[4, 0, origin[2]], 'R'], [[0, 4, origin[2]], 'C'], [[0, 0, origin[2] + 3], 'O']]) {
            line(g, [origin, end], g.colors.ink, 'categorical_axis', {width: .8}); g.label(end, text);
          }
          g.label([2, -1, origin[2]], 'Chart ' + (index + 1));
          Object.assign(record, {n, columns, values, rowGain, columnGain, outputGain, cells});
          primitives.push({kind: 'operation_relation', ...record});
        } else if (p.kind === 'graph') {
          const sourceNodes = p.nodes, xmin = Math.min(...sourceNodes.map(n => n.x)), xmax = Math.max(...sourceNodes.map(n => n.x));
          const ymin = Math.min(...sourceNodes.map(n => n.y)), ymax = Math.max(...sourceNodes.map(n => n.y));
          const xGain = 5 / Math.max(1, xmax - xmin), yGain = 4 / Math.max(1, ymax - ymin);
          const groups = [...new Set(sourceNodes.map(n => n.group ?? 0))];
          const nodes = sourceNodes.map((n, i) => ({...n, displayedLabel: String(i + 1), point: [(n.x - xmin) * xGain, (n.y - ymin) * yGain, origin[2] + .6 * groups.indexOf(n.group ?? 0)]}));
          const points = new Map(nodes.map(n => [n.key, n.point]));
          const edges = p.edges.map(edge => {
            const from = points.get(edge.from), to = points.get(edge.to);
            if (!from || !to) throw new Error('Algebra source edge has no named endpoint');
            line(g, [from, to], g.colors.teal, 'algebra_edge', {from: edge.from, to: edge.to, label: edge.label});
            return {...edge, points: [from, to]};
          });
          nodes.forEach(n => {
            g.sphere(n.point, n.selected ? .075 : .045, n.excluded ? g.colors.coral : n.selected ? g.colors.gold : g.colors.blue,
              {fidelity_kind: 'algebra_node', key: n.key});
            g.label([n.point[0], n.point[1] + .25, n.point[2]], n.displayedLabel);
          });
          g.label([2.5, -1, origin[2]], 'Chart ' + (index + 1));
          Object.assign(record, {nodes, edges, groups, xmin, ymin, xGain, yGain, groupDepthGain: .6});
          primitives.push({kind: 'algebra_graph', ...record});
        } else if (p.kind === 'points') {
          // These coordinates are actual integer input/output values, rather than graph layout.
          const xScale = Math.max(1, ...p.points.map(v => Math.abs(v.x)), ...p.xRange.map(Math.abs));
          const yScale = Math.max(1, ...p.points.map(v => Math.abs(v.y)), ...p.yRange.map(Math.abs));
          const xGain = 3 / xScale, yGain = 3 / yScale;
          const points = p.points.map(v => ({...v, point: [v.x * xGain, v.y * yGain, origin[2]]}));
          line(g, [[-3, 0, origin[2]], [3, 0, origin[2]]], g.colors.ink, 'integer_input_axis');
          line(g, [[0, -3, origin[2]], [0, 3, origin[2]]], g.colors.ink, 'integer_output_axis');
          // A line between adjacent integers would incorrectly add noninteger domain elements.
          points.forEach(v => g.sphere(v.point, .055, g.colors.blue, {fidelity_kind: 'integer_map', x: v.x, y: v.y}));
          g.label([3.5, 0, origin[2]], 'Integer n'); g.label([0, 3.5, origin[2]], 'Integer kn');
          Object.assign(record, {points, xGain, yGain, xScale, yScale});
          primitives.push({kind: 'integer_map', ...record});
        } else throw new Error('Unknown authored algebra chart');
        panels.push(record);
      });
      const parameters = a.controls.filter(c => !c.stations || c.stations.includes(m.state.station)).map(c => {
        const option = c.options?.find(o => (Array.isArray(o) ? o[0] : o.value) === m.state[c.key]);
        return c.label + ': ' + (option ? (Array.isArray(option) ? option[1] : option.label) : m.state[c.key]);
      }).join('. ');
      const calibration = panels.map(p => p.kind === 'points' ? 'Chart ' + (p.index + 1) + ': exact integer x gain ' + p.xGain.toPrecision(16) + ', y gain ' + p.yGain.toPrecision(16) + '.' : p.kind === 'table' ? 'Chart ' + (p.index + 1) + ': R=row label, C=column label, O=output label slot. Row-label gain ' + p.rowGain.toPrecision(16) + ', column-label gain ' + p.columnGain.toPrecision(16) + ', output-label-slot gain ' + p.outputGain.toPrecision(16) + '; output label slots ' + p.values.map((v, i) => i + '=' + String(v)).join(', ') + '.' : 'Chart ' + (p.index + 1) + ': declared graph-layout x gain ' + p.xGain.toPrecision(16) + ', y gain ' + p.yGain.toPrecision(16) + ', group separation gain 0.6. Node-label key: ' + p.nodes.map(n => n.displayedLabel + '=' + n.label).join('; ') + '.').join(' ');
      return {state: m.state, readout: m.readout + ' ' + parameters + '. ' + calibration,
        note: 'Every operation cell, named graph edge and discrete integer point comes from the same exact algebra activity. Group elements and output label slots are categorical; their spacing and ordering do not supply a metric on a group or ring. Coset depth separates named sets without implying physical separation. Integer-map points retain actual integer coordinates with listed gains; no intervening real inputs are added. Infinite domains and universal Sylow/kernel claims require the full proof ledger. Camera changes the view and preserves every active and inactive lesson parameter.',
        legend: [{label: 'Exact element / operation result', color: g.colors.blue}, {label: 'Preserved map / graph edge', color: g.colors.teal}, {label: 'Selected witness', color: g.colors.gold}],
        algebra: {state: m.state, active: m.active, proof: m.proof, panels, primitives}};
    }
  };
  if (typeof window !== 'undefined') window.PrimerAlgebraSpatialFamily = family;
  if (typeof module !== 'undefined' && module.exports) module.exports = family;
}());
