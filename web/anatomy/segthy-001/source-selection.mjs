/** Select only a literal label within one released native sweep. */
export function sourceSelection(search, cases) {
  const query = new URLSearchParams(search);
  const keys = ['volume', 'label', 'representation'];
  if (!keys.some(key => query.has(key))) return null;
  const fail = () => { const error = new Error('The link does not identify one released source sweep and label.'); error.name = 'SourceSelectionError'; throw error; };
  if (query.getAll('volume').length !== 1 || query.getAll('label').length !== 1
      || query.getAll('representation').length > 1) return fail();
  const raw = query.get('label');
  if (!/^[1-9][0-9]*$/.test(raw)) return fail();
  const volume = cases.find(row => row.id === query.get('volume'));
  const label = Number(raw);
  if (!volume || !volume.labels.some(row => row.code === label)) return fail();
  const representation = query.get('representation');
  if (representation !== null && !['clinical_image', 'model'].includes(representation)) return fail();
  return { volume: volume.id, label, representation };
}
