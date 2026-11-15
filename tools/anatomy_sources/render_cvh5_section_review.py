#!/usr/bin/env python3
"""Display every preserved source section; thumbnails never replace native source pixels."""
import argparse
import hashlib
import json
from pathlib import Path


def render(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    raw=(output/'source-review.json').read_bytes();review=json.loads(raw);figures=[]
    for start in range(0,len(review['sections']),16):
        selected=review['sections'][start:start+16]
        fig,axes=plt.subplots(4,4,figsize=(10,11),layout='constrained')
        fig.get_layout_engine().set(rect=(0,.04,1,.96))
        for ax in axes.flat:ax.set_axis_off()
        for ax,row in zip(axes.flat,selected):
            p=output/row['file']
            if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Source section differs')
            with Image.open(p) as native:ax.imshow(native,interpolation='nearest')
            ax.set_title('Original PDF page '+str(row['source_page']),fontsize=9)
        fig.suptitle('CVH5 | original cadaveric section context\nPage order retained; no MRI, tumour, spacing/axis registration or clinical approval',fontsize=11)
        fig.text(.5,.005,'Wu et al. 2015 | CC BY 4.0 | DOI 10.1371/journal.pone.0132226; correction 0140736\nDisplay thumbnails only; native section samples and original ICC remain unchanged',ha='center',fontsize=8)
        name=f'section-context-{start+1:03d}-{start+len(selected):03d}.png';p=output/name;fig.savefig(p,dpi=100);plt.close(fig)
        figures.append({'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_pages':[r['source_page'] for r in selected]})
    (output/'section-context-review.json').write_text(json.dumps({'source_review_sha256':hashlib.sha256(raw).hexdigest(),'figures':figures,'clinical_approval':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    render(p.parse_args().output)
