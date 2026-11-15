"""Independent original-archive, DICOM, XML, SEG and cell-boundary review.

Never rewrites source files or owner proof. This is source fidelity, not clinical
approval. Exact original per-instance/per-frame geometry remains authoritative.
"""
from pathlib import Path
from collections import Counter
import csv, gzip, hashlib, io, json, struct, sys, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.pulmonary_readout_review_guard import reconstruct_original_readout
PRIVATE=ROOT/'.research/pulmonary-intake-20261011'
sys.path.insert(0,str(PRIVATE/'python-deps'))
import pydicom
OUT=ROOT/'web/anatomy/lidc-idri-0525'
REVIEW=ROOT/'docs/pulmonary-nodule-independent-review-20261011'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def tag(e): return e.tag.rsplit('}',1)[-1]
def text(e,name): return next((x.text for x in e.iter() if tag(x)==name),None)
def unpack(row):
    raw=(OUT/row['file']).read_bytes()
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    if row.get('codec'):
        raw=gzip.decompress(raw)
        assert len(raw)==row['decoded_bytes'] and sha(raw)==row['decoded_sha256']
    return raw

def archive_dicom(name):
    with zipfile.ZipFile(OUT/name) as z:
        names=[n for n in z.namelist() if n.endswith('.dcm')]
        assert len(names)==1
        raw=z.read(names[0]);d=pydicom.dcmread(io.BytesIO(raw))
        return raw,d

def native_polygon(points):
    # Separate ray-crossing implementation, on integer source pixel centres.
    # Original XML contour samples are outside pixels and remain excluded.
    pts=np.asarray(points,dtype=int);lo=pts.min(0);hi=pts.max(0)
    yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];inside=np.zeros(xx.shape,bool)
    for (x1,y1),(x2,y2) in zip(pts,np.roll(pts,-1,axis=0)):
        if y1!=y2: inside ^= ((y1>yy)!=(y2>yy)) & (xx < x1+(yy-y1)*(x2-x1)/(y2-y1))
    mask=np.zeros((512,512),bool);mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1]=inside
    mask[pts[:,1],pts[:,0]]=False
    return mask

def contents(d):
    out=[]
    for q in getattr(d,'ContentSequence',[]): out.append(q);out.extend(contents(q))
    return out

def main():
    REVIEW.mkdir(exist_ok=True)
    proposal=json.loads((ROOT/'docs/pulmonary-nodule-source-review-20261011/integration-proposal.json').read_text())
    rows=proposal['runtime_files'] if 'runtime_files' in proposal else proposal['files']
    for r in rows:
        raw=(ROOT/r['path']).read_bytes()
        if r['path']=='web/anatomy/lidc-idri-0525/reference.js':raw=reconstruct_original_readout(raw)
        assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],r['path']
    m=json.loads((OUT/'manifest.json').read_text())
    for r in m['original_files']:unpack(r)
    with zipfile.ZipFile(PRIVATE/'LIDC-IDRI-0525-complete-with-license.zip') as z:
        names=[n for n in z.namelist() if n.endswith('.dcm')]
        assert len(names)==429
        assert z.read('LICENSE')==(OUT/'LICENSE').read_bytes()
        original={n:z.read(n) for n in names}
    checksums={r['Filename']:r['MD5Hash'] for r in csv.DictReader((OUT/'ct-source-md5.csv').read_text().splitlines())}
    assert set(original)==set(checksums)=={r['filename'] for r in m['ct']['slices']}
    ct=np.frombuffer(b''.join(unpack(c) for c in m['ct']['chunks']),dtype='<u2').reshape((429,512,512))
    assert ct.size==112459776 and sha(ct.tobytes())==m['ct']['decoded_sha256']
    assert [(c['first_native_slice'],c['stop_native_slice_exclusive']) for c in m['ct']['chunks']]==[(k,min(k+64,429)) for k in range(0,429,64)]
    by_sop={};headers=[]
    for k,r in enumerate(m['ct']['slices']):
        raw=original[r['filename']];assert raw==(OUT/'original-ct'/r['filename']).read_bytes()
        assert hashlib.md5(raw).hexdigest()==checksums[r['filename']]==r['md5']
        d=pydicom.dcmread(io.BytesIO(raw));assert np.array_equal(d.pixel_array,ct[k])
        assert np.array_equal(d.pixel_array,np.frombuffer(d.PixelData,dtype='<u2').reshape(512,512))
        assert [int(d.Rows),int(d.Columns),int(d.BitsAllocated),int(d.BitsStored),int(d.HighBit),int(d.PixelRepresentation)]==[512,512,16,12,11,0]
        assert list(map(float,d.ImagePositionPatient))==r['position_LPS_mm']==m['ct']['positions_LPS_mm'][k]
        assert list(map(float,d.ImageOrientationPatient))==r['orientation']==m['ct']['orientation']==[1,0,0,0,1,0]
        assert list(map(float,d.PixelSpacing))==r['pixel_spacing_mm']==m['ct']['pixel_spacing_mm']
        assert float(d.RescaleSlope)==r['slope']==m['ct']['slope'] and float(d.RescaleIntercept)==r['intercept']==m['ct']['intercept']
        assert float(d.SliceThickness)==r['thickness_mm']==0.75
        assert not hasattr(d,'SingleCollimationWidth') and not hasattr(d,'TotalCollimationWidth')
        assert d.SOPInstanceUID==r['sop_uid'] and d.SeriesInstanceUID==text(ET.parse(OUT/'original-0525.xml').getroot(),'SeriesInstanceUid')
        by_sop[str(d.SOPInstanceUID)]=k
        headers.append(dict(sop=str(d.SOPInstanceUID),position=r['position_LPS_mm'],orientation=r['orientation'],spacing=r['pixel_spacing_mm'],slope=r['slope'],intercept=r['intercept']))
    root=ET.parse(OUT/'original-0525.xml').getroot();sessions=[e for e in root if tag(e)=='readingSession'];marks=[]
    for si,s in enumerate(sessions):
        for mark in s:
            if tag(mark) not in ('nonNodule','unblindedReadNodule'):continue
            nid=text(mark,'noduleID') or text(mark,'nonNoduleID')
            r=next(q for q in m['xml_marks'] if q['session_index']==si and q['source_id']==nid)
            char=next((q for q in mark if tag(q)=='characteristics'),None)
            assert r['kind']==tag(mark) and r['characteristics']==({tag(q):q.text for q in char} if char is not None else {})
            rois=[q for q in mark if tag(q)=='roi']
            assert r['complete_contour']==(char is not None) and r['centroid_only']==(char is None)
            if tag(mark)=='nonNodule':
                assert len(r['rois'])==1 and r['rois'][0]['source_sop']==text(mark,'imageSOP_UID')
                assert r['rois'][0]['ct_slice']==by_sop[text(mark,'imageSOP_UID')]
                assert r['rois'][0]['points']==[[int(text(mark,'xCoord')),int(text(mark,'yCoord'))]]
            else:
                assert len(rois)==len(r['rois'])
                for q,v in zip(rois,r['rois']):
                    assert v['source_sop']==text(q,'imageSOP_UID') and v['ct_slice']==by_sop[v['source_sop']]
                    assert v['imageZposition']==text(q,'imageZposition') and v['inclusion']==text(q,'inclusion')
                    assert v['points']==[[int(text(p,'xCoord')),int(text(p,'yCoord'))] for p in q if tag(p)=='edgeMap']
                    assert float(v['imageZposition'])==m['ct']['positions_LPS_mm'][v['ct_slice']][2]
            marks.append((mark,r))
    assert len(sessions)==4 and len(marks)==33
    assert Counter('drawn' if r['complete_contour'] else r['kind'] for _,r in marks)=={'drawn':8,'unblindedReadNodule':8,'nonNodule':17}
    annotation_rows=[];gpu=[];total_samples=0
    for a in m['annotations']:
        raw,d=archive_dicom(a['source_archive']);assert sha(raw)==a['source_dicom_sha256']
        assert d.Modality=='SEG' and d.SOPInstanceUID==a['source_sop'] and str(d.ContentCreatorName)==a['source_content_creator']=='Reader1'
        seg=d.pixel_array;mask=np.frombuffer(unpack(a['mask']),dtype='u1').reshape(seg.shape)
        assert np.array_equal(seg,mask);total_samples+=mask.size
        measures=d.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0]
        assert list(map(float,measures.PixelSpacing))==a['pixel_spacing_mm']
        assert float(measures.SpacingBetweenSlices)==a['source_spacing_mm'] and float(measures.SliceThickness)==a['source_thickness_mm']
        orient=list(map(float,d.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient));assert orient==[1,0,0,0,1,0]
        origins=[];sops=[]
        for fi,f in enumerate(d.PerFrameFunctionalGroupsSequence):
            pos=list(map(float,f.PlanePositionSequence[0].ImagePositionPatient));sop=str(f.DerivationImageSequence[0].SourceImageSequence[0].ReferencedSOPInstanceUID)
            assert pos==a['source_frame_origins_LPS_mm'][fi] and sop==a['source_CT_sop_uids'][fi] and by_sop[sop]==a['source_CT_slice_indices'][fi]
            origins.append(pos);sops.append(sop)
        assert len(sops)==len(set(sops))==mask.shape[0]
        assert np.array_equal(np.asarray(origins)[:,:2],np.broadcast_to(origins[0][:2],(len(origins),2)))
        assert np.all(np.diff(np.asarray(origins)[:,2])>0)
        original,mark=next((q,r) for q,r in marks if r['source_id']==a['id'].removeprefix('annotation-') and r['complete_contour'])
        assert mark['session_index']==a['xml_session_index'] and mark['characteristics']==a['characteristics']
        xml=np.zeros_like(mask,bool);sop_frame={s:i for i,s in enumerate(sops)}
        for inclusion in ('TRUE','FALSE'):
            for roi in mark['rois']:
                if roi['inclusion']!=inclusion:continue
                plane=native_polygon(roi['points']);fi=sop_frame[roi['source_sop']]
                if inclusion=='TRUE':xml[fi]|=plane
                else:xml[fi]&=~plane;pts=np.asarray(roi['points']);xml[fi,pts[:,1],pts[:,0]]=False
        assert np.array_equal(xml,mask),(a['id'],int(np.count_nonzero(xml!=mask)))
        components=ndimage.label(mask,ndimage.generate_binary_structure(3,1))[1]
        assert components==a['six_connected_components'] and int(mask.sum())==a['occupied_voxels']
        exposed=[]
        for k,y,x in np.argwhere(mask):
            for axis in range(3):
                for sign in (-1,1):
                    p=[int(k),int(y),int(x)];p[axis]+=sign
                    if not all(0<=v<s for v,s in zip(p,mask.shape)) or not mask[tuple(p)]:exposed.append((int(k),int(y),int(x),axis,sign))
        records=np.frombuffer(unpack(a['face_records']),dtype='<i4').reshape(-1,5)
        assert Counter(map(tuple,records))==Counter(exposed)
        b=unpack(a['mesh']);magic,n,t=struct.unpack('<4sII',b[:12]);assert magic==b'LPC1'
        vertices=np.frombuffer(b[12:12+n*24],dtype='<f8').reshape(-1,3);faces=np.frombuffer(b[12+n*24:],dtype='<u4').reshape(-1,3)
        assert t==2*len(exposed)==a['mesh']['triangles'] and len(faces)==t and len(vertices)==n==a['mesh']['vertices']
        z=np.asarray(origins)[:,2];edges=np.r_[z[0]-float(measures.SpacingBetweenSlices)/2,(z[1:]+z[:-1])/2,z[-1]+float(measures.SpacingBetweenSlices)/2]
        expected=[]
        for k,y,x,axis,sign in records:
            ranges=[(origins[0][0]+(x-.5)*float(measures.PixelSpacing[1]),origins[0][0]+(x+.5)*float(measures.PixelSpacing[1])),(origins[0][1]+(y-.5)*float(measures.PixelSpacing[0]),origins[0][1]+(y+.5)*float(measures.PixelSpacing[0])),(edges[k],edges[k+1])]
            normal_axis=2-axis;other=[j for j in range(3) if j!=normal_axis]
            corners=[]
            for u,v in [(0,0),(1,0),(1,1),(0,1)]:
                p=[0.,0.,0.];p[normal_axis]=ranges[normal_axis][int(sign>0)];p[other[0]]=ranges[other[0]][u];p[other[1]]=ranges[other[1]][v];corners.append(tuple(p))
            expected.append(frozenset(corners))
        actual=[frozenset(tuple(vertices[j]) for j in set(faces[2*i])|set(faces[2*i+1])) for i in range(t//2)]
        assert Counter(expected)==Counter(actual)
        q=vertices[faces];norm=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);assert np.all(np.linalg.norm(norm,axis=1)>0)
        for i,record in enumerate(records): assert np.all(norm[2*i:2*i+2,2-record[3]]*record[4]>0)
        directed=Counter((int(v[i]),int(v[(i+1)%3])) for v in faces for i in range(3))
        assert all(directed[(b,a)]==count for (a,b),count in directed.items())
        nonmanifold_edges=sum(count>1 for (a,b),count in directed.items())//2
        cell_volume=sum(float(measures.PixelSpacing[0])*float(measures.PixelSpacing[1])*(edges[k+1]-edges[k]) for k,_,_ in np.argwhere(mask))
        centered=q-q[0,0];mesh_volume=float(np.einsum('ij,ij->i',centered[:,0],np.cross(centered[:,1],centered[:,2])).sum()/6)
        assert np.isclose(mesh_volume,cell_volume,rtol=1e-10,atol=1e-8),(a['id'],mesh_volume,cell_volume)
        srraw,sr=archive_dicom(a['source_SR']['original_archive']);assert sha(srraw)==a['source_SR']['original_dicom_sha256'] and sr.Modality=='SR'
        items={str(c.ConceptNameCodeSequence[0].CodeMeaning):c for c in contents(sr) if hasattr(c,'ConceptNameCodeSequence')}
        zs=sorted({float(r['imageZposition']) for r in mark['rois']});zedge=np.r_[zs[0]-(zs[1]-zs[0])/2,(np.asarray(zs[1:])+zs[:-1])/2,zs[-1]+(zs[-1]-zs[-2])/2]
        contour_vol=0;diam=0
        for r in mark['rois']:
            pts=np.asarray(r['points'],float)*np.asarray(m['ct']['pixel_spacing_mm'])[::-1];x,y=pts.T
            area=abs(float(np.sum(x*np.roll(y,-1)-y*np.roll(x,-1)))/2);j=zs.index(float(r['imageZposition']))
            contour_vol+=area*(zedge[j+1]-zedge[j])*(1 if r['inclusion']=='TRUE' else -1)
            diam=max(diam,float(np.max(np.linalg.norm(pts[:,None]-pts[None,:],axis=2))))
        sourcevol=float(items['Volume'].MeasuredValueSequence[0].NumericValue);sourcediam=float(items['Diameter'].MeasuredValueSequence[0].NumericValue)
        assert np.isclose(sourcevol,contour_vol,rtol=1e-6,atol=1e-5) and np.isclose(sourcediam,diam,rtol=1e-6,atol=1e-6)
        # GPU oracle uses original complete source-cell vertices/faces, independent
        # of viewer decode and model assembly; order is source mesh triangle order.
        bounds=np.asarray(a['mesh']['bounds_LPS_mm']);assert np.array_equal(bounds,np.stack([vertices.min(0),vertices.max(0)]))
        center=bounds.mean(0);radius=np.linalg.norm((bounds[1]-bounds[0])/2)
        interleaved=np.empty((t,3,6),dtype='<f4');interleaved[:,:,:3]=(q-center)/radius*.85;interleaved[:,:,3:]=norm[:,None,:]/np.linalg.norm(norm,axis=1)[:,None,None]
        gpu.append(dict(id=a['id'],bytes=interleaved.nbytes,sha256=sha(interleaved.tobytes()),vertices=n,triangles=t))
        annotation_rows.append(dict(id=a['id'],original_samples=int(mask.size),occupied_cells=int(mask.sum()),components=int(components),exposed_faces=len(exposed),triangles=t,original_content_creator=str(d.ContentCreatorName),XML_session=a['xml_session_index'],XML_exclusions=sum(r['inclusion']=='FALSE' for r in mark['rois']),balanced_oriented_cell_boundary=True,nonmanifold_shared_sampling_cell_edges=nonmanifold_edges,mesh_volume_mm3=mesh_volume,occupied_cell_volume_mm3=cell_volume,original_SR_contour_volume_mm3=sourcevol,independent_contour_volume_mm3=contour_vol,original_SR_maximal_axial_contour_diameter_mm=sourcediam))
    assert total_samples==19136512 and sum(r['triangles'] for r in annotation_rows)==12568
    # More source-oracle positions than the owner path; every plane hashes the
    # entire native RGB plane, including corners, arbitrary indices and all masks.
    positions=[[0,0,0],[511,511,428],[1,510,1],[510,1,427],[128,287,333],[256,256,214]]
    rng=np.random.default_rng(525);positions.extend(rng.integers([0,0,0],[512,512,429],size=(8,3)).tolist())
    oracles=[]
    for p in positions:
        rgb=[]
        for plane in [ct[:,:,p[0]][::-1],ct[:,p[1],:][::-1],ct[p[2]]]:
            hu=plane.astype(float)*m['ct']['slope']+m['ct']['intercept'];g=np.clip(np.floor((hu+1000)*255/1400+.5),0,255).astype('u1');rgba=np.empty(g.shape+(4,),dtype='u1');rgba[:,:,:3]=g[:,:,None];rgba[:,:,3]=255
            rgb.append(dict(width=g.shape[1],height=g.shape[0],sha256=sha(rgba.tobytes())))
        h=headers[p[2]];lps=[h['position'][0]+p[0]*h['spacing'][1],h['position'][1]+p[1]*h['spacing'][0],h['position'][2]]
        oracles.append(dict(cursor=p,planes=rgb,stored_integer=int(ct[p[2],p[1],p[0]]),HU=int(ct[p[2],p[1],p[0]])-1024,LPS=lps,SOP=h['sop']))
    overlay_oracles=[]
    for a in m['annotations']:
        _,d=archive_dicom(a['source_archive']);seg=d.pixel_array
        iz,iy,ix=np.nonzero(seg);indices=np.asarray(a['source_CT_slice_indices'])
        p=[int(np.floor(ix.mean()+.5)),int(np.floor(iy.mean()+.5)),int(np.floor(indices[iz].mean()+.5))]
        tint0=np.zeros((429,512),bool);tint0[indices,:]=seg[:,:,p[0]]
        tint1=np.zeros((429,512),bool);tint1[indices,:]=seg[:,p[1],:]
        tint2=seg[list(indices).index(p[2])].astype(bool) if p[2] in indices else np.zeros((512,512),bool)
        hashes=[]
        for plane,tint in zip([ct[:,:,p[0]][::-1],ct[:,p[1],:][::-1],ct[p[2]]],[tint0[::-1],tint1[::-1],tint2]):
            g=np.clip(np.floor((plane.astype(float)-1024+1000)*255/1400+.5),0,255).astype('u1');rgba=np.empty(g.shape+(4,),dtype='u1');rgba[:,:,:3]=g[:,:,None];rgba[:,:,3]=255
            for ch,color in enumerate([255,100,50]):rgba[:,:,ch][tint]=np.floor(g[tint]*.65+color*.35+.5).astype('u1')
            hashes.append(dict(width=g.shape[1],height=g.shape[0],sha256=sha(rgba.tobytes())))
        overlay_oracles.append(dict(annotation=a['id'],cursor=p,planes=hashes,source_link='original referenced CT SOP, no fitted registration'))
    result=dict(source_commit='aafe94142f517e1b7714f518c69f24b4171306fc',manifest_sha256=sha((OUT/'manifest.json').read_bytes()),integration_proposal_sha256=sha((ROOT/'docs/pulmonary-nodule-source-review-20261011/integration-proposal.json').read_bytes()),runtime_files=len(rows),full_original_CT_instances=429,full_original_CT_samples=int(ct.size),all_original_archive_CT_bodies_and_publisher_MD5_match=True,all_CT_IOP_IPP_spacing_slope_intercept_preserved=True,CT_nominal_reconstructed_thickness_mm=.75,acquired_collimation_verified=False,seven_complete_transport_chunks=True,XML_sessions=4,XML_marks=33,XML_drawn_annotations=8,XML_small_nodule_loci=8,XML_non_nodule_loci=17,XML_exclusion_contours=1,all_original_XML_values_match=True,complete_original_SEG_objects=8,complete_original_SR_objects=8,complete_original_SEG_samples=total_samples,annotations=annotation_rows,GPU_buffer_oracles=gpu,native_plane_oracles=oracles,native_overlay_oracles=overlay_oracles,normal_anatomy_bindings=[],clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False)
    current_js_sha=sha((OUT/'reference.js').read_bytes())
    output='source-oracle.json'
    if current_js_sha!='8444e3d0384bb9d0450ac414a52abd4bef61df851096de63004e37e531b02e04':
        result['bounded_current_readout_amendment']=dict(current_JS_sha256=current_js_sha,exact_original_JS_reconstructed=True,source_arrays_overlay_and_geometry_unchanged=True)
        output='source-oracle-readout-amended.json'
    (REVIEW/output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['annotations','GPU_buffer_oracles','native_plane_oracles','native_overlay_oracles']},indent=2))

if __name__=='__main__':main()
