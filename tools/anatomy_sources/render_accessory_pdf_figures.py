#!/usr/bin/env python3
"""Render complete published accessory-muscle figures, preserving PDF annotations.

Inputs are the original PDFs listed by PMC's documented 2026 Cloud Service.
This is deterministic PDF rasterization, not image synthesis or retouching.
"""
from pathlib import Path
import subprocess,math,json,hashlib,argparse
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
base=args.source_dir;out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
expected_pdfs = {
    'PMC4427770.1.pdf': '8c7da6dcd6f236304f6dfcc697435c86ca90fb981eac85a31744821be2a3b40d',
    'PMC7516695.1.pdf': 'a71114e45ca2fdf21b3537c73536de62c2360c336fb030a12e60505221294e9d',
    'PMC12468075.1.pdf': '102b77ed96700f45f169521cfc0fe59678c8493edc6548b4ecd40889efc71961',
}
for filename, digest in expected_pdfs.items():
    if hashlib.sha256((base / filename).read_bytes()).hexdigest() != digest:
        raise ValueError('Original PDF fingerprint mismatch: ' + filename)
figures=[('soleus-fig1','PMC7516695.1.pdf',3,300,[137.5,72.5,462.5,538]),('soleus-fig3','PMC7516695.1.pdf',5,300,[137,72.5,463,539]),('fdal-fig2','PMC4427770.1.pdf',2,600,[84,286.5,256.5,453.5]),('pq-fig1','PMC12468075.1.pdf',2,300,[147.5,72,398.5,259.5]),('pq-fig2','PMC12468075.1.pdf',4,300,[166.5,72.5,486,210])]
records=[]
for name,filename,page,dpi,bbox in figures:
 scale=dpi/72;x,y=map(lambda v:math.floor(v*scale),bbox[:2]);right,bottom=map(lambda v:math.ceil(v*scale),bbox[2:]);dest=out/name
 args=['pdftoppm','-f',str(page),'-l',str(page),'-r',str(dpi),'-x',str(x),'-y',str(y),'-W',str(right-x),'-H',str(bottom-y),'-png','-singlefile',str(base/filename),str(dest)]
 subprocess.run(args,check=True,capture_output=True)
 raw=dest.with_suffix('.png').read_bytes();size=Image.open(dest.with_suffix('.png')).size
 records.append(dict(name=name,pdf=filename,pdf_sha256=hashlib.sha256((base/filename).read_bytes()).hexdigest(),page=page,dpi=dpi,bbox_pdf_points=bbox,crop_pixels=[x,y,right-x,bottom-y],output=str(dest.with_suffix('.png')),width=size[0],height=size[1],sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),method='Poppler PDF rendering to lossless PNG; original image objects, vector arrows and panel lettering remain in their PDF positions. No learned upscaling or retouching.'))
 print(name,size,len(raw),flush=True)
(out/'rendered-figure-records.json').write_text(json.dumps(records,indent=2)+'\n')
