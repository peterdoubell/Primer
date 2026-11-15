/* Exact state-space coordinates; spatial offsets only arrange distinct charts. */
(function () {
  'use strict';
  const TAU = 2 * Math.PI;
  const line = (g, points, color, kind, extra = {}) => {
    if (points.length > 1) g.line(points, color, {width: 1.7, fidelity_kind: kind, ...extra});
  };
  const xyz = p => [p.x, p.y, p.z];
  const shifted = (p, o) => p.map((v, i) => v + o[i]);
  const matches = (state, conditions) => Object.entries(conditions).every(([key, values]) => values.includes(state[key]));
  function controls() {
    const a = window.PrimerPhysicsQuantumInfoLab;
    const options = values => values.map(o => Array.isArray(o) ? {value: o[0], label: o[1]} : o);
    return [{key: 'mode', label: 'Quantum information station', options: options(a.stations)},
      ...[...a.controls, ...a.choices].map(c => {
        const out = {...c, numericInput: !c.options, preserveExact: !c.options, visibleWhen: {mode: c.modes}};
        if (c.options) out.options = options(c.options);
        if (['thetaDeg', 'phiDeg', 'globalPhaseDeg'].includes(c.key)) out.visibleWhenAny = [
          {mode: c.modes.filter(mode => mode !== 'register')}, {mode: ['register'], preparation: ['tensor']}];
        if (c.key === 'gateAngleDeg') out.visibleWhen = {...out.visibleWhen, gate: ['Rx', 'Ry', 'Rz']};
        return out;
      })];
  }
  const family = {
    title: 'Quantum amplitudes, Bloch states and circuits',
    requires: 'PrimerPhysicsQuantumInfoLab', linkedStateKey: 'phys.5.quantum-info',
    initialFactory: () => ({...window.PrimerPhysicsQuantumInfoLab.initial}),
    normalize: raw => window.PrimerPhysicsQuantumInfoLab.normalize(raw),
    controlsFactory: controls,
    build(state, g) {
      const a = window.PrimerPhysicsQuantumInfoLab, m = a.build(state), d = m.geometry;
      const primitives = [], palette = [g.colors.teal, g.colors.blue, g.colors.coral];
      const record = (kind, data) => primitives.push({kind, ...data});
      // Bloch coordinates are dimensionless expectation values, not locations.
      d.blochVectors.forEach((v, i) => {
        const origin = [3.2 * i, 2, 0], color = palette[i % palette.length];
        for (let axis = 0; axis < 3; axis++) {
          const points = Array.from({length: 65}, (_, j) => {
            const p = [0, 0, 0]; p[(axis + 1) % 3] = Math.cos(TAU * j / 64); p[(axis + 2) % 3] = Math.sin(TAU * j / 64);
            return shifted(p, origin);
          });
          line(g, points, g.colors.ink, 'bloch_unit_circle', {width: .7});
          const end = [...origin]; end[axis] += 1.2;
          line(g, [origin, end], g.colors.ink, 'bloch_axis', {width: .7});
          g.label(end, ['x', 'y', 'z'][axis]);
        }
        const point = shifted(xyz(v), origin);
        line(g, [origin, point], color, 'bloch_vector', {key: v.key});
        g.sphere(point, .06, color, {fidelity_kind: 'bloch_endpoint', key: v.key});
        const label = m.state.mode === 'teleportation' ? v.key === 'input' ? 'Input' : v.key === 'bob-local' ? 'Before bits' : m.state.teleportStage === 'corrected' ? 'After bits' : 'Branch ' + m.current.selected.bits : v.key;
        g.label([origin[0], origin[1] + 1.65, 0], label);
        record('bloch', {key: v.key, value: xyz(v), origin, point, gain: 1});
      });
      d.trajectories.forEach(t => {
        const origin = t.key === 'grover-rotation' ? [0, 2, 0] : [3.2, 2, 0];
        const points = t.points.map(p => shifted(xyz(p), origin));
        line(g, points, g.colors.gold, 'state_trajectory', {key: t.key});
        record('trajectory', {key: t.key, origin, points, source: t.points, gain: 1});
        if (t.key === 'grover-rotation') {
          line(g, Array.from({length: 65}, (_, i) => shifted([Math.cos(TAU * i / 64), Math.sin(TAU * i / 64), 0], origin)), g.colors.ink, 'real_amplitude_unit_circle', {width: .7});
          const point = shifted([m.current.unmarkedAggregateAmplitude, m.current.markedAmplitude, 0], origin);
          line(g, [origin, point], g.colors.blue, 'grover_selected_vector');
          g.sphere(point, .07, g.colors.blue, {fidelity_kind: 'grover_selected'});
          g.label([0, 3.6, 0], 'Grover real amplitude plane');
          g.label([1.5, 2, 0], 'Unmarked aggregate');
          g.label([0, 3.15, 0], 'Marked amplitude');
          record('grover_selected', {origin, point, value: [m.current.unmarkedAggregateAmplitude, m.current.markedAmplitude, 0], gain: 1});
        }
      });
      const all = d.amplitudes, start = m.current.displayStart || 0;
      const visible = all.slice(start, start + 64), mixed = visible.some(row => row.densityDiagonal);
      const reducedGrover = m.state.mode === 'grover' && !m.current.actual;
      const dimension = reducedGrover ? 2 : m.current.dimension || m.current.N || Math.max(1, all.length);
      const indexScale = Math.max(1, dimension - 1), xGain = 6 / indexScale;
      const magnitude = Math.max(...visible.map(row => mixed ? row.probability : Math.max(Math.abs(row.re), Math.abs(row.im))), 0);
      const valueGain = magnitude > 0 ? Math.min(1e300, 1.5 / magnitude) : 1;
      const gainCapped = magnitude > 0 && 1.5 / magnitude > 1e300;
      const amplitudeOrigin = [0, -2, 0];
      visible.forEach(row => {
        const values = mixed ? [row.index, row.probability, 0] : [row.index, row.re, row.im];
        const point = shifted([values[0] * xGain, values[1] * valueGain, values[2] * valueGain], amplitudeOrigin);
        const base = shifted([values[0] * xGain, 0, 0], amplitudeOrigin);
        line(g, [base, point], g.colors.blue, mixed ? 'density_probability' : 'complex_amplitude', {basis: row.basis, index: row.index});
        g.sphere(point, .032, g.colors.blue, {fidelity_kind: mixed ? 'density_probability' : 'complex_amplitude', index: row.index});
        record(mixed ? 'density_probability' : 'complex_amplitude', {row, values, point, origin: amplitudeOrigin, xGain, valueGain});
      });
      if (visible.length) {
        line(g, [amplitudeOrigin, shifted([6, 0, 0], amplitudeOrigin)], g.colors.ink, 'basis_axis');
        line(g, [amplitudeOrigin, shifted([0, 1.5, 0], amplitudeOrigin)], g.colors.ink, 'real_axis');
        if (!mixed) line(g, [amplitudeOrigin, shifted([0, 0, 1.5], amplitudeOrigin)], g.colors.ink, 'imaginary_axis');
        g.label([3, -3.2, 0], mixed ? 'Diagonal probabilities' : 'Complex coefficients');
        g.label([6.1, -2, 0], reducedGrover ? 'Reduced slot' : 'Index');
        g.label([0, -.3, 0], mixed ? 'P' : 'Re');
        if (!mixed) g.label([0, -2, 1.75], 'Im');
      }
      const circuitOrigin = [0, -5, 0], circuit = d.circuit || [];
      const qubits = circuit.length ? 1 + Math.max(...circuit.map(c => Math.max(c.qubit, c.target ?? 0))) : 0;
      const steps = circuit.length ? Math.max(...circuit.map(c => c.step)) : 0;
      for (let q = 0; q < qubits; q++) {
        line(g, [[0, -5 - q, 0], [2 * (steps + 1), -5 - q, 0]], g.colors.ink, 'circuit_wire', {qubit: q});
        g.label([-.6, -5 - q, 0], 'q' + q);
      }
      circuit.forEach(c => {
        const point = shifted([2 * c.step, -c.qubit, 0], circuitOrigin);
        g.sphere(point, .08, g.colors.teal, {fidelity_kind: 'circuit_gate', step: c.step, qubit: c.qubit});
        const shortLabel = c.label.includes('CNOT') ? 'CX' : c.label.startsWith('Measure') ? 'M' : c.classicalFrom ? 'ZᑫXᵃ' : c.label === 'Bell A' ? 'A' : c.label === 'Bell B' ? 'B' : c.label;
        g.label(shifted([0, .32, 0], point), shortLabel);
        if (c.target !== undefined) {
          const target = shifted([2 * c.step, -c.target, 0], circuitOrigin);
          line(g, [point, target], g.colors.blue, 'controlled_gate', {control: c.qubit, target: c.target});
          g.sphere(target, .06, g.colors.blue, {fidelity_kind: 'controlled_target', qubit: c.target});
          g.label(shifted([0, .28, 0], target), 'X');
        }
        for (const from of c.classicalFrom || []) line(g, [shifted([2 * (c.step - 1), -from, 0], circuitOrigin), point], g.colors.gold, 'classical_message', {from, target: c.qubit});
        record('circuit_gate', {source: c, point, origin: circuitOrigin, stepGain: 2, qubitGain: -1});
      });
      const active = controls().filter(c => (!c.visibleWhen || matches(m.state, c.visibleWhen)) && (!c.visibleWhenAny || c.visibleWhenAny.some(group => matches(m.state, group))));
      const parameters = active.map(c => c.label + ': ' + (c.options ? c.options.find(o => o.value === m.state[c.key])?.label : m.state[c.key]) + (c.unit ? ' ' + c.unit : '')).join('. ');
      const calibration = (reducedGrover ? 'Two exact reduced basis slots, not N individual database amplitudes. Reduced slot gain ' : 'Basis index gain ') + xGain.toPrecision(16) + '; ' + (mixed ? 'probability' : 'Re/Im amplitude') + ' gain ' + valueGain.toPrecision(16) + '. Visible rows ' + start + '–' + Math.max(start, start + visible.length - 1) + ' of ' + all.length + '; the complete source arrays and full normalization remain in the activity. Bloch gains are exactly one. Circuit step gain 2 and qubit gain −1 arrange discrete operations, not distances or duration.';
      const branchScope = m.state.mode === 'teleportation' ? ' Teleportation comparison: Before bits is always Bob’s unconditioned I/2 reference before the classical record. ' + (m.state.teleportStage === 'corrected' ? 'After bits is the restored input after feed-forward; correcting all four branches restores the same state.' : 'The selected branch vector is a conditional comparison; at initial and Bell-unitary checkpoints it is hypothetical until Alice measures. The full current Q,A,B amplitudes retain the selected checkpoint.') : '';
      return {state: m.state, readout: m.readout + ' ' + parameters + '. ' + calibration + branchScope,
        note: m.note + ' Bloch vectors use their actual three expectation values; an unconditioned local mixture stays distinct from a selected branch. Grover’s real amplitude plane is a symmetry reduction, not a physical qubit Bloch sphere. The displayed trajectory covers the last amplification iteration only. Complex amplitude phase is a state-coordinate representation; a common phase leaves physical predictions invariant. Separate chart origins and circuit wires are layout. ZᑫXᵃ applies Xᵃ first and then Zᑫ. Display arithmetic is float64; extremely small values can underflow or coincide with a chart axis. ' + (gainCapped ? 'The display gain is capped at 1e300; the nonzero source values remain in the activity even when their plotted displacements are visually unresolved. ' : '') + 'Camera movement changes the view and preserves the complete circuit state.',
        legend: [{label: 'Input / operation', color: g.colors.teal}, {label: 'Output / exact coefficient', color: g.colors.blue}, {label: 'Gate path / classical message', color: g.colors.gold}],
        quantumInfo: {state: m.state, current: m.current, geometry: d, primitives, calibration: {indexScale, xGain, valueGain, gainCapped, start, visible: visible.length, complete: all.length}}};
    }
  };
  if (typeof window !== 'undefined') window.PrimerQuantumInformationSpatialFamily = family;
  if (typeof module !== 'undefined' && module.exports) module.exports = family;
}());
