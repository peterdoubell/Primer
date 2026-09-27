#!/usr/bin/env python3
"""Render a source-frame component identity audit; no clinical approval inferred."""
import sys,json,gzip
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.split_malaya_knee_components import parse
m=json.loads((ROOT/'web/anatomy/msk-mri-knee/manifest.json').read_text())
out=Path('/tmp/primer-msk-sources/high-fidelity/malaya-knee/component-audit');out.mkdir(exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(14,7),facecolor='white')
for ax,parentkey,title in zip(axes,['um-knee-meniscus-knee','um-knee-cartilage-tibia'],['Native meniscus components','Native tibial cartilage components']):
 for key,color in [('um-knee-bone-tibia','#dedbd1'),('um-knee-bone-fibula','#bdb7a7')]:
  p=m['parts'][key];v,_,f=parse(gzip.decompress((ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes()));v=np.array(v);f=np.array(f);tri=v[f];tri=tri[np.max(tri[:,:,2],axis=1)>-367];ax.add_collection(PolyCollection(tri[:,:,:2]*[1,-1],facecolor=color,edgecolor='none',alpha=.25))
 for p,color in zip(m['parts'][parentkey]['components'],['#7655ac','#cf8133']):
  v,_,f=parse(gzip.decompress((ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes()));v=np.array(v);f=np.array(f);tri=v[f]
  ax.add_collection(PolyCollection(tri[:,:,:2]*[1,-1],facecolor=color,edgecolor=color,linewidth=.1,alpha=.9))
  center=v.mean(axis=0);ax.text(center[0],-center[1],p['name'].replace(' tibial plateau','\ntibial plateau'),ha='center',va='center',fontsize=10,color='black',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
 ax.set(xlim=(-110,0),ylim=(-78,15),aspect='equal',xlabel='Native LPS X (mm): lateral ← → medial',ylabel='Anterior ↑ / posterior ↓')
 ax.set_title(title+' · right knee, superior projection')
 ax.grid(alpha=.2)
fig.suptitle('Source component identity QA — no fitted, cut or invented anatomy',fontsize=14)
fig.text(.5,.01,'Faint tibia/fibula preserve the original source frame. Names interpret complete disconnected components; finer anatomy remains unvalidated.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.94));fig.savefig(out/'components-superior.png',dpi=140)
print(out/'components-superior.png')
