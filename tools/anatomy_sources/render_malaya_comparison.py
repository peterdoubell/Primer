#!/usr/bin/env python3
"""Research-only visual comparison and source MRI/segmentation registration view."""
import json,pathlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from check_staged_meshes import read
from verify_malaya_registration import load_nrrd
R=pathlib.Path('/tmp/primer-msk-sources/high-fidelity');m=json.loads((R/'malaya-knee/manifest.json').read_text());z=json.loads(pathlib.Path('/tmp/primer-msk-sources/staged/manifest.json').read_text())
colors={'bone':'#ccccbf','cartilage':'#57aaab','meniscus':'#876ac1','ligament':'#d89330','tendon':'#d8594e'}

def add(ax,part,color,alpha=1):
 _,p,n,ix=read(part['file']);tri=p[ix];display=tri[:,:,[0,1,2]]
 poly=Poly3DCollection(display,facecolor=color,edgecolor='none',alpha=alpha,zsort='average');ax.add_collection3d(poly)
 return display.reshape(-1,3)

def frame(ax,p):
 lo,hi=p.min(0),p.max(0);center=(lo+hi)/2;r=max(hi-lo)*.58
 ax.set_xlim(center[0]-r,center[0]+r);ax.set_ylim(center[1]-r,center[1]+r);ax.set_zlim(center[2]-r,center[2]+r);ax.set_box_aspect((1,1,1));ax.view_init(elev=28,azim=-65);ax.set_axis_off()

fig=plt.figure(figsize=(13,5),facecolor='white')
a=fig.add_subplot(1,2,1,projection='3d');b=fig.add_subplot(1,2,2,projection='3d')
p=next(p for p in m['parts'].values() if p['layer']=='meniscus');pts=add(b,p,colors['meniscus']);frame(b,pts);b.set_title('MRI-derived Malaya menisci\n5,204 original facets; 2 surfaces + zero-area artifact',fontsize=12)
zs=[p for p in z['parts'].values() if p['name'] in ['Medial meniscus.r','Lateral meniscus.r']]
points=[]
for p in zs:
 _,v,n,ix=read(p['file']);v=v[:,[0,2,1]];v[:,1]*=-1;tri=v[ix];a.add_collection3d(Poly3DCollection(tri,facecolor=colors['meniscus'],edgecolor='#665284',linewidth=.3,alpha=.9));points.append(v)
frame(a,np.concatenate(points));a.set_title('Z-Anatomy menisci\n752 facets; separate source reference subject',fontsize=12)
fig.text(.5,.025,'Independent source frames. Each view is centered and fitted for inspection; no anatomical registration between datasets.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.06,1,1));fig.savefig(R/'malaya-knee/meniscus-source-comparison.png',dpi=150)

fig=plt.figure(figsize=(10,8),facecolor='white');ax=fig.add_subplot(projection='3d');points=[]
for p in m['parts'].values():
 if p['layer']=='bone':continue
 points.append(add(ax,p,colors[p['layer']],.75 if p['layer']=='cartilage' else .95))
frame(ax,np.concatenate(points));ax.set_title('Malaya source knee: cartilage volumes, menisci, ligaments and extensor mechanism\nNative LPS geometry, no fitting or invented structures',fontsize=12)
fig.text(.5,.04,'Teal: cartilage · Purple: menisci · Gold: ligaments · Red: quadriceps tendon\nAuthor-derived reference geometry; independent clinical adequacy review remains required.',ha='center',fontsize=10);fig.savefig(R/'malaya-knee/source-soft-tissues.png',dpi=130)

# Direct physical-coordinate overlay, with explicit nearest-plane centers.
ih,image,iv,io=load_nrrd(R/'um-registration/19 RT T2 FS spc_SAG_iso (KNEE).nrrd');sh,segments,sv,so=load_nrrd(R/'um-registration/Segmentation.seg.nrrd')
acl=next(p for p in m['parts'].values() if p['source_name']=='Ligament_ACL');x=float(np.mean(np.array(acl['bounds'])[:,0]));ik=int(round((x-io[0])/iv[2][0]));sk=int(round((x-so[0])/sv[3][0]));ix=float(io[0]+iv[2][0]*ik);sx=float(so[0]+sv[3][0]*sk)
plane=image[:,:,ik].T;extent=[io[1]-.5*iv[0][1],io[1]+(image.shape[0]-.5)*iv[0][1],io[2]+(image.shape[1]-.5)*iv[1][2],io[2]-.5*iv[1][2]]
fig,axes=plt.subplots(1,2,figsize=(12,7),facecolor='white');vmax=float(np.percentile(plane,99.5));yy=so[1]+np.arange(segments.shape[1])*sv[1][1];zz=so[2]+np.arange(segments.shape[2])*sv[2][2]
for ax in axes:ax.imshow(plane,cmap='gray',origin='upper',extent=extent,vmin=0,vmax=vmax);ax.set_xlim(-65,85);ax.set_ylim(-400,-250);ax.set_xlabel('LPS Y (posterior), mm');ax.set_ylabel('LPS Z (superior), mm')
for p in m['parts'].values():
 if p['layer'] not in ['cartilage','meniscus','ligament','tendon']:continue
 seg=p.get('source_segmentation')
 if not seg:continue
 mask=segments[seg['layer'],:,:,sk].T==seg['label_value']
 if mask.any():axes[1].contour(yy,zz,mask,levels=[.5],colors=[colors[p['layer']]],linewidths=1)
axes[0].set_title('Public T2 fat-suppressed knee NRRD');axes[1].set_title('Source segmentation contours, native LPS')
fig.suptitle(f'Registration QA only · sagittal image X={ix:.3f} mm / nearest label plane X={sx:.3f} mm',fontsize=12)
fig.text(.5,.015,'Contours are the authors’ labels, not new diagnoses. Different voxel grids; no image resampling or anatomical fitting.\nThis is a technical source-correspondence check, not approval for clinical reporting.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.07,1,.95));fig.savefig(R/'malaya-knee/source-mri-label-overlay-qa.png',dpi=150)
(R/'malaya-knee/overlay-qa.json').write_text(json.dumps({'image_x_mm':ix,'label_x_mm':sx,'plane_difference_mm':abs(ix-sx),'requested_x_mm':x,'image_source':str(R/'um-registration/19 RT T2 FS spc_SAG_iso (KNEE).nrrd'),'segmentation_source':str(R/'um-registration/Segmentation.seg.nrrd'),'method':'nearest source sagittal plane in native LPS; no fitted transform'},indent=2)+'\n')
print('Rendered meniscus comparison, soft-tissue view and native-coordinate MRI/label QA overlay')
