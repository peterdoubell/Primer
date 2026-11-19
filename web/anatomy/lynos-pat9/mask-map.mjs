// The five label arrays share the source CT grid. Count each membership even
// when two independently drawn structures occupy the same sampled cell.
export const overlapColour = [252, 249, 239];
const background = [22, 30, 38];

export function paintMaskMap(raster, crop, nodes, nearby, labels) {
  const counts = new Map();
  let occupied = 0;
  let overlaps = 0;
  for (let row = 0; row < crop.height; row += 1) {
    const start = (crop.y0 + row) * nodes.width + crop.x0;
    for (let column = 0; column < crop.width; column += 1) {
      const index = start + column;
      const nodeId = nodes.pixels[index];
      let members = 0;
      let colour = background;
      if (nodeId) {
        const node = labels.get(nodeId);
        colour = node.color;
        counts.set(node, (counts.get(node) || 0) + 1);
        members++;
      }
      for (const { annotation, section } of nearby) {
        if (!section.pixels[index]) continue;
        colour = annotation.color;
        counts.set(annotation, (counts.get(annotation) || 0) + 1);
        members++;
      }
      if (members) occupied++;
      if (members > 1) {
        overlaps++;
        colour = overlapColour;
      }
      const offset = 4 * (row * crop.width + column);
      raster[offset] = colour[0];
      raster[offset + 1] = colour[1];
      raster[offset + 2] = colour[2];
      raster[offset + 3] = 255;
    }
  }
  return { counts, occupied, overlaps };
}

export function maskNamesAt(section, x, y, labels) {
  const index = y * section.nodes.width + x;
  const node = labels.get(section.nodes.pixels[index]);
  const names = node ? [node.name] : [];
  for (const entry of section.landmarks) {
    if (entry.section.pixels[index]) names.push(entry.annotation.name);
  }
  return names;
}
