#!/usr/bin/env python3
"""Render source meshes as standalone QA figures; never publishes app content."""
import json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from check_staged_meshes import read,CACHE

manifest=json.loads((CACHE/'staged/manifest.json').read_text())
colors={'bone':'#c8c9ca','labrum':'#067da5','meniscus':'#9564b2','ligament':'#d99b32','capsule':'#87abb7','muscle':'#9b4640','tendon':'#faf4df','nerve':'#dbc039','bursa':'#74c0bd','fat':'#e6bc5d','fibrocartilage':'#9564b2','tendon-sheath':'#74c0bd','fascia':'#a3b4a8'}
fig=plt.figure(figsize=(15,10),facecolor='#f5f5f1')
for idx,(region,spec) in enumerate(manifest['regions'].items()):
 ax=fig.add_subplot(2,3,idx+1,projection='3d');ax.set_facecolor('#f5f5f1')
 box=np.array(spec['focus_bounds']);center=box.mean(0);width=max(np.ptp(box,axis=0))*1.25;low=center-width/2;high=center+width/2
 for pid in spec['parts']:
  p=manifest['parts'][pid]
  if p['source_category'] not in {'bones','joints'} or p['layer']=='capsule':continue
  _,v,n,ix=read(p['file']);tri=v[ix];keep=((tri>=low)&(tri<=high)).all(axis=2).any(axis=1);tri=tri[keep]
  if not len(tri):continue
  display=tri[:,:,[0,2,1]]
  bone=p['layer']=='bone'
  poly=Poly3DCollection(display,facecolor=colors[p['layer']],edgecolor='#65481b' if p['triangles']<=40 else 'none',linewidth=.45 if p['triangles']<=40 else 0,alpha=.20 if bone else .85,zsort='average')
  ax.add_collection3d(poly)
 ax.set_xlim(low[0],high[0]);ax.set_ylim(low[2],high[2]);ax.set_zlim(low[1],high[1]);ax.set_box_aspect((1,1,1));ax.view_init(elev=20,azim=60);ax.set_axis_off()
 ax.set_title(region.title()+' · native source geometry',fontsize=13,pad=0)
fig.suptitle('Z-Anatomy MSK source audit — no generated anatomy or registration fitting',fontsize=16,y=.98)
fig.text(.5,.026,'Gray: bones · Gold: ligament meshes · Blue: labra · Purple: menisci\nCropped view for inspection. Surface detail and clinical completeness are not established by this plot.',ha='center',fontsize=11)
fig.subplots_adjust(left=.025,right=.975,top=.94,bottom=.08,hspace=.01,wspace=.02)
fig.savefig(CACHE/'staged/six-joint-source-audit.png',dpi=150)
# Isolated low-fidelity examples must remain visible in the audit.
fig=plt.figure(figsize=(12,4),facecolor='#f5f5f1')
for i,name in enumerate(['Scapholunate interosseous ligament.r','Anterior talofibular ligament.r','Medial meniscus.r']):
 p=next(p for p in manifest['parts'].values() if p['name']==name);_,v,n,ix=read(p['file']);ax=fig.add_subplot(1,3,i+1,projection='3d');tri=v[ix][:,:,[0,2,1]]
 ax.add_collection3d(Poly3DCollection(tri,facecolor=colors[p['layer']],edgecolor='#444444',linewidth=.5,alpha=.9));lo=tri.reshape(-1,3).min(0);hi=tri.reshape(-1,3).max(0);c=(lo+hi)/2;r=max(hi-lo)*.6
 ax.set_xlim(c[0]-r,c[0]+r);ax.set_ylim(c[1]-r,c[1]+r);ax.set_zlim(c[2]-r,c[2]+r);ax.set_box_aspect((1,1,1));ax.view_init(elev=22,azim=40);ax.set_axis_off();ax.set_title(name.removesuffix('.r')+'\n'+str(p['triangles'])+' native triangles',fontsize=11)
fig.subplots_adjust(left=.02,right=.98,top=.88,bottom=.04,wspace=.01);fig.savefig(CACHE/'staged/fidelity-limits.png',dpi=150)
print('Rendered six-joint-source-audit.png and fidelity-limits.png')
