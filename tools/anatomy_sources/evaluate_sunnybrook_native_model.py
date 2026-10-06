#!/usr/bin/env python3
"""Evaluate the original FE basis and compare with Zinc; preserve source image shifts separately."""
import argparse,hashlib,itertools,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT,parse_exnode,parse_exelem

def verified_model_inputs():
    source=json.loads((OUT/'original-parameter-source-review.json').read_text());records=[]
    for record in source['source_model_members']:
        path=(OUT/record['file']).resolve()
        if not path.is_relative_to(OUT.resolve()) or not path.is_file():raise ValueError('Original model file missing or outside source packet')
        raw=path.read_bytes()
        if len(raw)!=record['bytes'] or hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Original model file differs: '+record['file'])
        records.append({'file':record['file'],'sha256':record['sha256']})
    return records

def hermite(t):
    return ((2*t**3-3*t*t+1,t**3-2*t*t+t),(-2*t**3+3*t*t,t**3-t*t))

def evaluate_prolate(nodes,element,xi):
    x,y,z=xi;hx,hy=hermite(x),hermite(y);lx,ly,lz=(1-x,x),(1-y,y),(1-z,z)
    lam=mu=theta=0.;angles=[]
    for local,ident in enumerate(element['source_node_ids']):
        n=nodes[ident-1];a,b,c=local%2,(local//2)%2,local//4;sf=element['source_scale_factors']
        v,d1,d2,d12=[n['lambda_and_derivatives'][k]*sf[4*local+k] for k in range(4)]
        lam+=(hx[a][0]*hy[b][0]*v+hx[a][1]*hy[b][0]*d1+hx[a][0]*hy[b][1]*d2+hx[a][1]*hy[b][1]*d12)*lz[c]
        w=lx[a]*ly[b]*lz[c];mu+=w*n['mu']*sf[32+local];angles.append(n['theta']*sf[32+local])
    for left in [0,2,4,6]:
        while angles[left+1]>angles[left]:angles[left+1]-=2*math.pi
    for local,angle in enumerate(angles):theta+=lx[local%2]*ly[(local//2)%2]*lz[local//4]*angle
    return [lam,mu,theta]

def prolate_to_cartesian(p,focus):
    lam,mu,theta=p
    return [focus*math.cosh(lam)*math.cos(mu),focus*math.sinh(lam)*math.sin(mu)*math.cos(theta),focus*math.sinh(lam)*math.sin(mu)*math.sin(theta)]

def patient_matrix(serialized):
    if len(serialized)!=16:raise ValueError('Source projection requires 16 values')
    return [[serialized[j*4+i] for j in range(4)] for i in range(4)]

def project(point,matrix):
    v=point+[1.];out=[sum(a*b for a,b in zip(row,v)) for row in matrix]
    if abs(out[3])<1e-12:raise ValueError('Invalid homogeneous projection')
    return [value/out[3] for value in out[:3]]

def image_shift_review():
    ns={'c':'http://www.cardiacatlas.org'};xml=ET.parse(OUT/'original-case-model/model_SCD0000101_ao.xml');link=json.loads((OUT/'native-cine-linkage-review.json').read_text());by_sop={r['sop_uid']:r for r in link['linked_images']};groups={}
    for ref in xml.findall('.//c:Input/c:Image',ns):
        native=by_sop[ref.get('sopiuid')];pos=ref.find('c:ImagePosition',ns);orient=ref.find('c:ImageOrientation',ns)
        if orient is not None:raise ValueError('Additional source orientation override requires explicit handling')
        original=native['native']['image_position_patient'];adjusted=[float(pos.find('c:'+axis,ns).text) for axis in 'xyz'] if pos is not None else original[:]
        row={'frame':int(ref.get('frame')),'sop_uid':ref.get('sopiuid'),'native_image_position_patient':original,'original_XML_image_position':adjusted,'source_XML_position_override_present':pos is not None,'original_XML_minus_DICOM_position':[a-b for a,b in zip(adjusted,original)],'source_positions_changed_by_us':False}
        groups.setdefault(ref.get('label'),[]).append(row)
    result=[]
    for label,rows in sorted(groups.items()):
        shifts={tuple(r['original_XML_minus_DICOM_position']) for r in rows}
        if len(shifts)!=1:raise ValueError('Source plane adjustment changes over frames')
        delta=rows[0]['original_XML_minus_DICOM_position'];result.append({'label':label,'source_shift_length_in_declared_DICOM_mm':math.sqrt(sum(v*v for v in delta)),'frames':rows})
    return result

def evaluate():
    from cmlibs.zinc.context import Context
    from cmlibs.zinc.field import Field
    original_inputs=verified_model_inputs();source=json.loads((OUT/'original-parameter-source-review.json').read_text());elements=parse_exelem((OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes());matrix=patient_matrix(source['original_transform_16_values']);grid=list(itertools.product([0.,.125,.37,.63,.875,1.],[0.,.125,.37,.63,.875,1.],[0.,.5,1.]));summary=[];samples=[]
    for phase in range(1,21):
        path=OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode';focus,nodes=parse_exnode(path.read_bytes());context=Context('OriginalSunnybrook');region=context.getDefaultRegion()
        if region.readFile(str(path))!=1 or region.readFile(str(OUT/'original-case-model/GlobalHermiteParam.exelem'))!=1:raise ValueError('Zinc rejected original FE files')
        fm=region.findChildByName('heart').getFieldmodule();field=fm.findFieldByName('coordinates');mesh=fm.findMeshByDimension(3);cache=fm.createFieldcache();rc=fm.createFieldCoordinateTransformation(field);trans=fm.createFieldConstant([v for row in matrix for v in row]);patient=fm.createFieldProjection(rc,trans)
        if mesh.getSize()!=16 or field.getCoordinateSystemFocus()!=focus:raise ValueError('Zinc model scope/focus differs')
        maxima=[0.,0.,0.];count=0
        for element in elements:
            ze=mesh.findElementByIdentifier(element['element_id'])
            for xi in grid:
                cache.setMeshLocation(ze,list(xi));expected=evaluate_prolate(nodes,element,xi);expected_rc=prolate_to_cartesian(expected,focus);expected_patient=project(expected_rc,matrix)
                values=[]
                for f in [field,rc,patient]:
                    status,value=f.evaluateReal(cache,3)
                    if status!=1:raise ValueError('Zinc evaluation failed')
                    values.append(value)
                # Different angular branches must still be checked modulo a full turn.
                ps_error=max(abs(expected[i]-values[0][i]) if i<2 else abs(math.remainder(expected[i]-values[0][i],2*math.pi)) for i in range(3))
                errors=[ps_error,max(abs(a-b) for a,b in zip(expected_rc,values[1])),max(abs(a-b) for a,b in zip(expected_patient,values[2]))];maxima=[max(a,b) for a,b in zip(maxima,errors)];count+=1
                if max(errors)>1e-8:raise ValueError(f'Independent basis/coordinate/projection mismatch phase {phase}, element {element["element_id"]}, xi {xi}: {errors}')
                if xi in [(0.,0.,0.),(.37,.63,.5),(1.,1.,1.)]:samples.append({'source_file_phase':phase,'element_id':element['element_id'],'xi':list(xi),'independent_prolate':expected,'zinc_prolate':values[0],'independent_patient':expected_patient,'zinc_patient':values[2]})
        logger=context.getLogger()
        if logger.getNumberOfMessages():raise ValueError('Zinc emitted source load/evaluation messages')
        summary.append({'source_file_phase':phase,'evaluated_points':count,'maximum_prolate_error_modulo_angular_turn':maxima[0],'maximum_cartesian_error':maxima[1],'maximum_patient_projection_error':maxima[2]})
    ordering={'same_xi_surface_pairs':0,'xi3_0_lambda_less_than_xi3_1':0,'xi3_0_lambda_greater_than_xi3_1':0,'lambda_equal':0}
    for phase in range(1,21):
        _,nodes=parse_exnode((OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode').read_bytes())
        for element in elements:
            for u,v in itertools.product([0.,.125,.37,.63,.875,1.],repeat=2):
                a=evaluate_prolate(nodes,element,[u,v,0.])[0];b=evaluate_prolate(nodes,element,[u,v,1.])[0];ordering['same_xi_surface_pairs']+=1
                key='lambda_equal' if abs(a-b)<1e-12 else 'xi3_0_lambda_less_than_xi3_1' if a<b else 'xi3_0_lambda_greater_than_xi3_1';ordering[key]+=1
    shifts=image_shift_review();out={'evaluator_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_model_inputs':original_inputs,'source_surface_parameter_order_review':ordering,'surface_tissue_role_validation':'unresolved_original_conversion_vs_inspected_CAP_renderer_conflict','clinical_epicardial_endocardial_roles_assigned':False,'zinc_version':list(context.getVersion()[1]),'original_source_elements':16,'all_original_phases_evaluated':20,'sample_grid_per_element':len(grid),'independent_scalar_basis_vs_Zinc':summary,'samples':samples,'original_XML_transposed_projection_matrix':matrix,'original_XML_plane_adjustments':shifts,'original_source_files_changed':False,'new_fitting_smoothing_or_plane_adjustments_applied':False,'source_model_basis_and_coordinate_projection_numerically_compared':True,'spatial_registration_to_unadjusted_native_DICOM_validated':False,'contour_native_pixel_convention_or_phase_validated':False,'clinical_function_or_geometry_approved':False,'runtime_promoted':False}
    (OUT/'native-model-evaluation-review.json').write_text(json.dumps(out,indent=2)+'\n');print('All 20 source phases compared against Zinc at',sum(r['evaluated_points'] for r in summary),'points; source image shifts retained separately.')
if __name__=='__main__':evaluate()
