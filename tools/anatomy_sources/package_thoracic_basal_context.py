"""Build a complete same-case lung/liver/spleen correspondence viewer for review."""
import argparse
import json
import shutil
from pathlib import Path

from tools.anatomy_sources.package_thoracic_lung_candidate import package as preserve
from tools.anatomy_sources.package_thoracic_lung_viewer import package as buffers

ROOT = Path(__file__).resolve().parents[2]


def render_correspondence(output, proof, masks):
    """Render whole original index planes and source-label boundaries at native pitch."""
    import nibabel as nib
    import numpy as np
    from scipy import ndimage
    from PIL import Image, ImageDraw
    ct = np.asarray(nib.load(output / proof['records'][0]['file']).dataobj.get_unscaled())
    colors = [(0, 220, 255), (70, 240, 70), (235, 70, 220), (255, 160, 30),
              (245, 230, 20), (255, 90, 70), (155, 120, 255)]
    canvas = Image.new('RGB', (1260, 1120), '#101722')
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 16), 's0028: original CT planes with unchanged lung, liver and spleen label boundaries', fill='white')
    draw.text((20, 38), 'Source values window -160 to 240; source axes only. No HU, tissue-layer or clinical approval inferred.', fill='white')
    selections = [('Liver fragment context', [154, 144, 234]), ('Spleen fragment context', [92, 136, 230])]
    for row, (title, point) in enumerate(selections):
        for col, axis in enumerate([2, 1, 0]):
            a, b = [i for i in range(3) if i != axis]
            extract = lambda array: np.flip(np.take(array, point[axis], axis=axis).T, axis=0)
            plane = extract(ct)
            gray = np.clip(np.rint((plane.astype(float)+160)*255/400), 0, 255).astype('uint8')
            rgb = np.repeat(gray[:, :, None], 3, axis=2)
            for mask, color in zip(masks, colors):
                part = extract(mask)
                edge = part & ~ndimage.binary_erosion(part, structure=ndimage.generate_binary_structure(2, 1))
                rgb[edge] = color
            x, y = col*420+20, row*480+100
            draw.text((x, y-32), title, fill='white')
            draw.text((x, y-16), f'Index axis {axis} = {point[axis]}; horizontal {a}, vertical {b}', fill='white')
            canvas.paste(Image.fromarray(rgb), (x, y))
            px, py = x+point[a], y+plane.shape[0]-1-point[b]
            draw.ellipse((px-6, py-6, px+6, py+6), outline='white', width=1)
    for i, record in enumerate(proof['records'][1:]):
        x, y = 20+(i % 4)*310, 1068+(i // 4)*20
        draw.rectangle((x, y, x+10, y+10), fill=colors[i])
        draw.text((x+16, y), record['label'].replace('_', ' '), fill='white')
    canvas.save(output / 'basal-source-correspondence.png')


def package(source, output):
    preserve(source, output)
    proof = json.loads((output / 'source-review.json').read_text())
    names = [r.get('label') for r in proof['records'][1:]]
    if names != ['lung_upper_lobe_left', 'lung_lower_lobe_left', 'lung_upper_lobe_right',
                 'lung_middle_lobe_right', 'lung_lower_lobe_right', 'liver', 'spleen']:
        raise ValueError('Complete original basal context labels required')
    shutil.copyfile(source / 'basal-context-acquisition.json', output / 'basal-context-acquisition.json')
    buffers(output)
    template = ROOT / 'docs/thoracic-lung-source-review-s0028'
    shutil.copyfile(template / 'viewer.css', output / 'viewer.css')
    volume = (template / 'volume-review.js').read_text()
    volume = volume.replace('[245,230,20]]', '[245,230,20],[255,90,70],[155,120,255]]')
    volume = volume.replace('and five unchanged binary labels', 'and seven unchanged binary labels')
    volume = volume.replace('new Option(r.label,i)));const count', "new Option(r.label,i)));$('level').value='5';const count")
    (output / 'volume-review.js').write_text(volume)
    surface = (template / 'surface-review.js').read_text()
    surface = surface.replace('[.96,.9,.08]]', '[.96,.9,.08],[1,.35,.27],[.61,.47,1]]')
    (output / 'surface-review.js').write_text(surface)
    html = (template / 'index.html').read_text()
    html = html.replace('s0028 lung source correspondence', 's0028 lung-base organ correspondence')
    html = html.replace('five same-case lung labels', 'five same-case lung labels, liver and spleen labels')
    html = html.replace('Selected lobe', 'Selected source organ').replace('All five lobes', 'All seven source parts')
    html = html.replace('by these five labels', 'by these seven labels')
    html = html.replace('<p id="scope"></p>', '<p>The liver and spleen labels provide same-case anatomical context for basal lung assessment. They do not establish an ultrasound acoustic path, organ motion, diaphragm identity or a current-patient finding. A label interface is not a tissue capsule. The original liver label includes a detached two-voxel component, and the spleen label a detached one-voxel component under face connectivity. Both are retained and need anatomical review; they are not identified as accessory organs.</p><p id="scope"></p>')
    (output / 'index.html').write_text(html)
    proof['pairwise_context_overlap_voxels'] = []
    import nibabel as nib
    import numpy as np
    from scipy import ndimage
    masks = [np.asarray(nib.load(output / r['file']).dataobj.get_unscaled(), dtype=bool)
             for r in proof['records'][1:]]
    for row, mask in zip(proof['records'][1:], masks):
        components, count = ndimage.label(mask, ndimage.generate_binary_structure(3, 1))
        sizes = np.bincount(components.ravel())[1:]
        row['component_voxels_6'] = sorted(sizes.tolist(), reverse=True)
        row['component_identification_policy'] = 'Connectivity components are source label fragments, not independently identified anatomical structures.'
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            proof['pairwise_context_overlap_voxels'].append({
                'labels': [names[i], names[j]], 'voxels': int(np.logical_and(masks[i], masks[j]).sum())})
    proof['intended_context'] = 'Same-case basal lung, liver and spleen spatial review; no ultrasound registration or tissue-layer inference.'
    (output / 'source-review.json').write_text(json.dumps(proof, indent=2) + '\n')
    render_correspondence(output, proof, masks)
    print('Seven source labels preserved,', sum(r['triangles'] for r in proof['records'][1:]), 'interface triangles')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.source_root, args.output)
