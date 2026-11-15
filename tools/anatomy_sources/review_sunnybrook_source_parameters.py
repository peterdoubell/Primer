#!/usr/bin/env python3
"""Retain original Sunnybrook case model/contour parameters without invented geometry or timing."""
import argparse,csv,hashlib,json,math,re,zipfile,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/sunnybrook-native-source-review';CASE='SCD0000101'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse_exnode(raw):
    text=raw.decode();match=re.search(r'prolate spheroidal, focus=\s*([\d.eE+-]+)',text)
    if not match:raise ValueError('Explicit original coordinate system missing')
    expected=['lambda.  Value index= 1, #Derivatives= 3 (d/ds1,d/ds2,d2/ds1ds2)', 'mu.  Value index= 5, #Derivatives= 0', 'theta.  Value index= 6, #Derivatives= 0']
    if not all(header in text for header in expected):raise ValueError('Original coordinate field layout differs')
    focus=float(match.group(1));
    if not math.isfinite(focus) or focus<=0:raise ValueError('Invalid original focal length')
    parts=re.split(r'Node:\s*(\d+)\s*',text);nodes=[]
    for i in range(1,len(parts),2):
        id=int(parts[i]);values=[float(x) for x in parts[i+1].split()]
        if len(values)!=6 or not all(math.isfinite(v) for v in values):raise ValueError('Original node values differ')
        nodes.append({'node_id':id,'lambda_and_derivatives':values[:4],'mu':values[4],'theta':values[5]})
    if [r['node_id'] for r in nodes]!=list(range(1,41)):raise ValueError('Original model node set differs')
    return focus,nodes

def parse_exelem(raw):
    text=raw.decode();volume=text.split('Shape.  Dimension=3',1)[1]
    for required in ['c.Hermite*c.Hermite*l.Lagrange, #Scale factors=32','l.Lagrange*l.Lagrange*l.Lagrange, #Scale factors= 8','theta.  l.Lagrange*l.Lagrange*l.Lagrange, decreasing in xi1']:
        if required not in volume:raise ValueError('Original element basis differs')
    parts=re.split(r'Element:\s*(\d+) 0 0',volume);elements=[]
    for i in range(1,len(parts),2):
        body=parts[i+1];nodepart=body.split('Nodes:',1)[1];nodes=[int(v) for v in nodepart.split('Scale factors:',1)[0].split()]
        factors=[float(v) for v in nodepart.split('Scale factors:',1)[1].split()]
        if len(nodes)!=8 or any(n<1 or n>40 for n in nodes) or len(factors)!=40 or not all(math.isfinite(v) for v in factors):raise ValueError('Original element layout differs')
        elements.append({'element_id':int(parts[i]),'source_node_ids':nodes,'source_scale_factors':factors})
    if [e['element_id'] for e in elements]!=list(range(1,17)):raise ValueError('Original element set differs')
    return elements

def review(root):
    OUT.mkdir(parents=True,exist_ok=True);original=json.loads((root/'small-source-acquisition.json').read_text());meta=[]
    for entry in original:
        raw=(root/entry['file']).read_bytes()
        if sha(raw)!=entry['sha256']:raise ValueError('Acquired source archive changed')
        meta.append(entry)
    clinical=list(csv.DictReader((root/'patient-data.csv').read_text(encoding='utf-8-sig').splitlines()));case=next(r for r in clinical if r['PatientID']==CASE)
    if case['OriginalID']!='SC-HF-I-1' or case['Pathology']!='Heart failure with infarct':raise ValueError('Source patient mapping differs')
    rows=[];frames=[]
    with zipfile.ZipFile(root/'lv-models.zip') as z:
        names=[n for n in z.namelist() if n.startswith('SCD_CAPModels/'+CASE+'/') and not n.endswith('/') and '.DS_Store' not in n]
        if len(names)!=22:raise ValueError('Original case model selection differs')
        for name in names:
            raw=z.read(name);target=OUT/'original-case-model'/name.split('/')[-1];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);rows.append({'archive':'lv-models.zip','member':name,'file':str(target.relative_to(OUT)),'bytes':len(raw),'sha256':sha(raw),'zip_crc_verified':True})
            if name.endswith('.exnode'):
                phase=int(re.search(r'_(\d+)\.model\.exnode$',name).group(1));focus,nodes=parse_exnode(raw);frames.append({'source_file_phase':phase,'focus':focus,'nodes':nodes})
        elements=parse_exelem(z.read(next(n for n in names if n.endswith('.exelem'))))
        xml_name=next(n for n in names if n.endswith('.xml'));x=E.fromstring(z.read(xml_name));ns={'cap':'http://www.cardiacatlas.org'};output=x.find('cap:Output',ns);inputs=x.find('cap:Input',ns)
        frame_refs=[{'frame':int(n.get('frame')),'file':n.text} for n in output.findall('cap:Exnode',ns)];image_refs=[{'frame':int(n.get('frame')),'label':n.get('label'),'slice':int(n.get('slice')),'series_uid':n.get('seriesiuid'),'sop_uid':n.get('sopiuid')} for n in inputs.findall('cap:Image',ns)]
        transform=[float(v) for v in output.get('transformation_matrix').split()]
        if len(transform)!=16 or not all(math.isfinite(v) for v in transform):raise ValueError('Original transform differs')
        provenance=[{'tag':n.tag.split('}')[-1],'value':n.text} for n in x.findall('.//cap:provenanceDetail/*',ns)]
    contour_rows=[]
    with zipfile.ZipFile(root/'manual-contours.zip') as z:
        for name in ['SCD_ManualContours/CC0_License.htm','SCD_ManualContours/README.txt']:
            raw=z.read(name);(OUT/name.split('/')[-1]).write_bytes(raw)
        for name in z.namelist():
            if '/SC-HF-I-01/' not in name or not name.endswith('.txt'):continue
            raw=z.read(name);points=[[float(v) for v in line.split()] for line in raw.decode().splitlines() if line.strip()]
            if not points or any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in points):raise ValueError('Original contour dimensions differ')
            target=OUT/'original-manual-contours'/name.split('/')[-1];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);contour_rows.append({'archive_member':name,'file':str(target.relative_to(OUT)),'sha256':sha(raw),'bytes':len(raw),'points':len(points),'kind':re.search(r'-([ipo]\d?contour)-',name).group(1),'original_pixel_index_range':[[min(p[i] for p in points) for i in range(2)],[max(p[i] for p in points) for i in range(2)]],'zip_crc_verified':True})
    (OUT/'original-element-topology.json').write_text(json.dumps({'lambda_basis':'cubic_Hermite_x_cubic_Hermite_x_linear_Lagrange','mu_basis':'linear_Lagrange_x_linear_Lagrange_x_linear_Lagrange','theta_basis':'linear_Lagrange_x_linear_Lagrange_x_linear_Lagrange','theta_modification':'decreasing_in_xi1','source_elements':elements,'source_connectivity_or_scale_factors_changed':False,'surface_tessellation_or_clinical_geometry_validated':False},indent=2)+'\n')
    frames.sort(key=lambda r:r['source_file_phase'])
    if [r['source_file_phase'] for r in frames]!=list(range(1,21)) or {r['frame'] for r in frame_refs}!=set(range(20)):raise ValueError('Original phase mapping differs')
    (OUT/'original-model-parameters.json').write_text(json.dumps({'coordinate_system':'original_prolate_spheroidal','lambda_fields':['value','d_ds1','d_ds2','d2_ds1ds2'],'frames':frames,'source_coordinates_changed':False,'cartesian_conversion_or_mesh_generated':False},indent=2)+'\n')
    report={'source_url':'https://www.cardiacatlas.org/sunnybrook-cardiac-data/','license':'CC0 1.0 Universal','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','attribution':'Radau P, Lu Y, Connelly K, Paul G, Dick AJ, Wright GA. Evaluation Framework for Algorithms Segmenting Short Axis Cardiac MRI, 2009. Data contributed by Perry Radau/Sunnybrook Health Sciences Centre; CAP distribution.',
        'primary_page_sha256':sha((root/'sunnybrook-primary-page.html').read_bytes()),'source_archives':meta,'source_clinical_record':case,'source_clinical_records':len(clinical),'source_model_members':rows,'source_manual_contours':contour_rows,'source_frame_refs':frame_refs,'source_image_refs':image_refs,'original_output_interval':output.get('interval'),'interval_converted_to_milliseconds':False,'original_focal_length':output.get('focallength'),'original_transform_16_values':transform,'transform_interpretation_independently_validated':False,'source_conversion_provenance':provenance,
        'source_40_node_parameters_preserved_per_phase':True,'all_20_source_model_phases_preserved':True,'source_original_model_definition_preserved':True,
        'native_image_linkage_verified':False,'physical_calibration_independently_verified':False,'model_motion_is_original_native_cine':False,'full_myocardial_wall_layer_or_valve_geometry_verified':False,'complete_anatomical_validation':False,'clinical_approval':False,'runtime_promoted':False,
        'limitations':['Source exnodes are prolate parameters/derivatives, not Cartesian patient coordinates; original model fitting/conversion and interpolation basis need independent review.',
            'XML interval 0.05 is not assumed 50 ms; actual DICOM timing/phase linkage remains to be checked.',
            'Original contour pixel indices/names are retained; native image match and index convention remain unverified.',
            'Source cohort/pathology descriptions are not current universal diagnostic thresholds or independently confirmed LGE/function.',
            'No source model smoothing/fitting/repair/Cartesian conversion or new surface was applied; no full cine-derived geometry is claimed.']}
    (OUT/'original-parameter-source-review.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'small-source-acquisition.json').write_bytes((root/'small-source-acquisition.json').read_bytes());(OUT/'patient-data.csv').write_bytes((root/'patient-data.csv').read_bytes())
    print('20 original prolate model phases and',len(contour_rows),'manual contours preserved; native linkage/basis/calibration pending.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);review(p.parse_args().source_root)
