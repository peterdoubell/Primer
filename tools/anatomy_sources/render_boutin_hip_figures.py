"""Render complete reviewed Boutin hip figures; does not mutate the runtime catalog."""
import argparse
from pathlib import Path
import hashlib,json,subprocess,math
from PIL import Image,ImageCms
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-pdf',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
src=args.source_pdf
assert hashlib.sha256(src.read_bytes()).hexdigest()=='ebf3ddd047e34db724c2dd8cdf7529070e9b18e284ed8ada569244cff794c49d'
out=args.output_dir; out.mkdir(parents=True,exist_ok=True); profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes();(out/'render-srgb.icc').write_bytes(profile)
reports=[]
for fig,page,box in [('6.5',3,(74,467,521,673)),('6.7',4,(49,297,546,499))]:
 x,y,r,b=box; scale=300/72; left,top=math.floor(x*scale),math.floor(y*scale); width,height=math.ceil(r*scale)-left,math.ceil(b*scale)-top
 name='hip-tendon-boutin-fig'+fig.replace('.','-'); target=out/name
 cmd=['/opt/homebrew/bin/pdftoppm','-f',str(page),'-l',str(page),'-singlefile','-r','300','-x',str(left),'-y',str(top),'-W',str(width),'-H',str(height),'-displayprofile',str(out/'render-srgb.icc'),'-png',str(src),str(target)]
 subprocess.run(cmd,check=True)
 p=target.with_suffix('.png')
 with Image.open(p) as im:
  im.load(); im.save(p,icc_profile=profile)
 reports.append({'figure':fig,'source_pdf_page':page,'source_pdf_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'bounds_points_top_left':box,'render_dpi':300,'render_crop_pixels':[left,top,width,height],'width':width,'height':height,'output_file':p.name,'output_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'Poppler PDF-aware complete figure render into explicit sRGB; lossless PNG packaging embeds same display profile. Rendered resampling, not unchanged native image bytes. No anatomical editing.','command':cmd,'source_resolution_limit':'About 150 effective PPI; rendering at 300 DPI does not add anatomical detail.'})
(out/'figure-rendering.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
