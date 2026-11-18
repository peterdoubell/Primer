// William Labov, “The Social Stratification of (r) in New York Department
// Stores,” Table 13.1 in the source linked by index.html. Each cell lists
// clear (r-1), clear (r-0), doubtful, and no data, in that order.
export const STORES = [
  {
    name: 'Saks', interviews: 68,
    fourth: [[17,39,4,8], [16,24,4,24]],
    floor: [[31,18,5,14], [21,12,4,31]],
  },
  {
    name: 'Macy’s', interviews: 125,
    fourth: [[33,81,0,11], [13,48,1,63]],
    floor: [[48,62,3,12], [31,20,0,74]],
  },
  {
    name: 'S. Klein', interviews: 71,
    fourth: [[3,63,1,4], [6,40,3,22]],
    floor: [[5,59,1,6], [7,33,3,28]],
  },
];

export const REPLIES = ['First reply', 'Careful repetition'];

export function observations(word, measure) {
  return STORES.map(store => ({
    name: store.name,
    interviews: store.interviews,
    replies: store[word].map(([present, absent, doubtful, missing]) => {
      const clear = present + absent;
      const part = measure === 'pronounced' ? present : clear;
      const whole = measure === 'pronounced' ? clear : store.interviews;
      return { present, absent, doubtful, missing, part, whole, proportion: part / whole };
    }),
  }));
}

export function largestChange(groups, measure) {
  const changes = groups.map((group, index) => {
    const [first, repeat] = group.replies.map(row => row.proportion);
    return { index, name: group.name, first, repeat, points: 100 * (repeat - first) };
  });
  return changes.reduce((leader, row) =>
    (measure === 'pronounced' ? row.points > leader.points : row.points < leader.points) ? row : leader);
}
