#!/usr/bin/env python3
"""Preserve full original consensus figures and table artwork, with separate case/role limits."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
INV='ra.mri-endometriosis';PREFIX='open-endometriosis-esur-2025-';SOURCE='https://pmc.ncbi.nlm.nih.gov/articles/PMC12559084/'
# Original PDF page, Poppler image index, object identity.
FIGURES={1:(4,2,41),2:(5,3,57),3:(8,16,79),4:(10,17,101),5:(11,18,105),6:(13,19,116)}
TABLES=list(zip('abcdefghijkl',[6]*5+[7]*5+[8]*2,range(4,16),[61,62,63,64,65,69,70,71,72,73,77,78]))
TABLE_TITLES=['Bladder sites','Proximal round ligament','Torus and proximal uterosacrals','Retrouterine space and external adenomyosis','Posterior vagina and rectovaginal space','Rectum and rectosigmoid','Distal round ligament','Mediolateral parametrium','Ureteric relationship','Posterolateral and neural relationships','Source lateral pelvic relationship','Source upper-abdominal / diaphragm diagram']
ROLES={1:dict.fromkeys('abc','MRI'),2:{'whole':'Schematic'},3:dict.fromkeys('abcd','MRI'),4:{**dict.fromkeys('abcdefghij','MRI'),'k':'Clinical photograph'},5:dict.fromkeys('abcdef','MRI'),6:{**dict.fromkeys('abcdefhi','MRI'),'g':'Clinical photograph','j':'Endoscopy'}}
CASES={1:{'35_year_woman':['a','b','c']},2:{},3:{'29_year_woman':['a','b'],'27_year_woman':['c','d']},4:{'35_year_woman_USL':['a'],'17_year_girl_USL':['b'],'27_year_woman_USL':['c','d','e'],'35_year_woman_RVS':['f','g','h'],'30_year_woman_vagina':['i','j','k']},5:{'rectal_case_age_not_supplied':['a','b','c'],'different_multifocal_case_age_not_supplied':['d','e','f']},6:{'31_year_woman_inguinal':['a','b'],'40_year_woman_scar':['c','d'],'31_year_woman_umbilicus':['e','f','g'],'32_year_woman_cecum':['h'],'appendiceal_case_identity_not_supplied':['i','j']}}
TITLES={1:'Source bilateral ovarian endometriomas and displaced ovaries',2:'Source conceptual reporting compartments',3:'Separate source bladder and proximal round-ligament cases',4:'Separate uterosacral, rectovaginal and vaginal source cases',5:'Separate rectal and multifocal bowel source cases',6:'Separate inguinal, scar, umbilical and bowel source cases'}
ISSUES={3:'The original caption assigns the axial round-ligament view to a while the displayed axial panel is d. Original caption/labels are retained; no corrected acquisition metadata is invented.',5:'The original caption contains the malformed token (&^HJYUa) beside its distance illustration. The dashed annotation is retained; no independently calibrated distance or registration is supplied.'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def package(source):
 from PIL import Image
 from pypdf import PdfReader
 from pypdf.generic import IndirectObject
 from primer import radiology_catalog as catalog
 from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
 from tools.check_static_raster_inventory import inventory
 meta_raw=(source/'article-metadata.json').read_bytes();meta=json.loads(meta_raw)
 assert meta['pmcid']=='PMC12559084' and not meta['is_retracted'] and meta['license_code']=='CC BY'
 xml=(source/'article.xml').read_bytes();pdf=(source/'article.pdf').read_bytes()
 for key,raw in [('xml_url',xml),('pdf_url',pdf)]:assert hashlib.md5(raw).hexdigest()==parse_qs(urlparse(meta[key]).query)['md5'][0]
 tree=E.fromstring(xml);permissions=tree.find('.//article-meta/permissions');assert 'creativecommons.org/licenses/by/4.0/' in E.tostring(permissions,encoding='unicode')
 authors=', '.join(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib/name'))
 authors+=' and the ESUR endometriosis working group'
 out=ROOT/'docs/endometriosis-source-review';out.mkdir(exist_ok=True)
 (out/'original-article.xml').write_bytes(xml);(out/'original-metadata.json').write_bytes(meta_raw)
 records=[];rows=[];assets=[];reader=PdfReader(source/'article.pdf')
 table=tree.find('.//table-wrap[@id="Tab2"]');source_table_rows=list(table.findall('.//tr'))
 selected=[]
 for n,(page,index,obj) in FIGURES.items():
  fig=tree.find('.//fig[@id="Fig'+str(n)+'"]');caption=' '.join(''.join(fig.find('caption').itertext()).split())
  assert fig.find('attrib') is None and fig.find('permissions') is None
  assert not any(x in caption.lower() for x in ['reprinted','reproduced','courtesy','adapted from'])
  selected.append(('fig'+str(n),page,index,obj,caption,ROLES[n],CASES[n],TITLES[n],n,ISSUES.get(n,''),{}))
 for i,(letter,page,index,obj) in enumerate(TABLES):
  graphic=table.find('.//inline-graphic[@id="'+['d33e971','d33e980','d33e992','d33e999','d33e1009','d33e1023','d33e1037','d33e1048','d33e1057','d33e1072','d33e1079','d33e1091'][i]+'"]')
  row=next(tr for tr in source_table_rows if graphic in list(tr.iter()))
  caption=' '.join(''.join(row.itertext()).split());cells=[dict(td.attrib) for td in list(row)]
  scope='Complete original table artwork; source row context is retained. Source schematic marks are conceptual lesions, not native tissue, patient coordinates or MRI.'
  if letter=='d':scope+=' The source image includes external adenomyosis as well as the retrouterine space; it is not a single tissue boundary.'
  if letter=='k':scope+=' Source row refers to nerves; the diagram is a broad pelvic relationship, not a complete independently verified nerve map.'
  if letter=='l':scope+=' The source image cell spans extra-pelvic rows (wall, digestive and diaphragm); the displayed upper-abdominal diagram must not be relabelled as a scar or bowel lesion.'
  selected.append(('table2-'+letter,page,index,obj,caption,{'whole':'Schematic'},{},'Original Table 2 artwork · '+TABLE_TITLES[i],2,scope,{'source_table':2,'source_table_panel':letter,'source_table_graphic':graphic.get('{http://www.w3.org/1999/xlink}href'),'source_table_row_cells':cells}))
 for key,page,index,oid,caption,roles,cases,title,n,issue,extras in selected:
  obj=reader.get_object(IndirectObject(oid,0,reader));assert oid in {r.idnum for r in reader.pages[page-1]['/Resources']['/XObject'].values()}
  assert obj.get('/Decode') is None and obj.get('/SMask') is None and obj.get('/Mask') is None and obj['/BitsPerComponent']==8
  jpeg=str(obj['/Filter'])=='/DCTDecode';ext='.jpg' if jpeg else '.png';master=source/'pdf-masters'/('native-'+str(index).zfill(3)+ext);raw=master.read_bytes()
  with Image.open(master) as im:
   im.load();pixels=im.tobytes();mode=im.mode;dimensions=list(im.size)
  assert dimensions==[obj['/Width'],obj['/Height']]
  assert str(obj['/ColorSpace']) in ['/DeviceGray','/DeviceRGB'];assert mode==('L' if str(obj['/ColorSpace'])=='/DeviceGray' else 'RGB')
  if jpeg:assert raw==obj._data
  else:assert pixels==obj.get_data()
  ident=PREFIX+key;local='web/reference-media/radiology-open/endometriosis-esur-2025-'+key+ext;(ROOT/local).write_bytes(raw)
  scheme=all(v=='Schematic' for v in roles.values());clinical=[p for p,v in roles.items() if v=='MRI']
  context={'setting':'conceptual' if scheme else 'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported' if scheme else 'mixed_or_not_reported'},'extent':'local','depicted_state':'conceptual_source_compartment_or_lesion_schematic' if scheme else 'source_endometriosis_case_examples','selected_panels':['whole'] if scheme else clinical,'all_source_panels':list(roles),'panel_types':roles,'source_case_groups':cases,'different_panels_assumed_same_patient':not scheme and len(cases)==1,'different_figures_assumed_same_patient':False,'source_panels_independently_registered':False,'native_acquisition_arrays_included':False,'independent_calibrated_measurements_verified':False,'biological_3d_model_created_from_artwork':False}
  if cases:context['population']['source_cases']=list(cases)
  if key=='fig4':context['population']['contains_source_adolescent_case']=True
  if issue:context['source_scope_issue']=issue
  credit=authors+'. '+meta['title']+'. DOI '+meta['doi']+'. '+('Table 2 artwork '+key[-1] if key.startswith('table') else 'Figure '+str(n))+'. CC BY4.0. '+('Original complete JPEG stream' if jpeg else 'Lossless PNG of every original decoded PDF sample')+' preserved; no crop, resizing, enhancement or annotation changes. Original Keydiag logos, when present, are retained as source artwork; no endorsement is asserted.'
  limits='Published local views and source conceptual artwork are not a complete acquired MRI, separately segmented tissues, an independently verified 3D anatomy model or a current-patient finding. Distinct cases, sequences and non-MRI observations are kept separate. No new diagnosis, calibrated measurement, every-structure coverage or clinical approval is supplied. '+issue
  row={'id':ident,'kind':'schematic' if scheme else 'clinical-image','modality':'Schematic' if scheme else 'MRI','figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':dimensions[0],'height':dimensions[1],'source_url':SOURCE,'figure_url':SOURCE+('#Tab2' if key.startswith('table') else '#Fig'+str(n)),'asset_source_url':meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'),'caption':title+'. Complete original source artwork and annotations.','alt':title+'; complete original source figure.','source_caption_full':caption,'source_context':context,'image_state':context['depicted_state'],'limits':limits,'structures_visible':['Source-local original named structures or schematic relationships; full reporting anatomy unapproved'],'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':credit,'rights_reviewed_on':'2026-10-10','rights_review':'Original publisher article/figure grant, exact PDF identities/samples and source case/role limits reviewed; no separate restrictive credit found. Keydiag artwork is retained within the licensed source, not reconstructed as anatomy.',**extras}
  if scheme:row['schematic_panels']=['whole'];row['schematic_structures_visible']=row['structures_visible'];row['schematic_limits']=limits
  else:row['clinical_panels']=clinical
  ancillary=[{'kind':kind,'panels':[p for p,v in roles.items() if v==kind],'structures_visible':['Separate source '+kind+' observation'],'limits':'Separate non-MRI source evidence; not a native MRI image or current examination.'+(' The Figure6 j operative view is source-described laparoscopy, not pelvic MRI.' if key=='fig6' and kind=='Endoscopy' else '')} for kind in sorted(set(roles.values())-{'Schematic','MRI'})]
  if ancillary:row['ancillary_panels']=ancillary
  catalog._validate_source_panel_roles(row);rows.append(row)
  records.append({'id':ident,'source_PDF_page':page,'source_PDF_object':oid,'source_Poppler_image_index':index,'source_PDF_filter':str(obj['/Filter']),'source_PDF_color_space':str(obj['/ColorSpace']),'source_complete_stream_or_samples_equal_to_independent_Poppler':True,'decoded_pixel_sha256':sha(pixels),'sha256':sha(raw),'dimensions':dimensions,'pixel_mode':mode,'visually_inspected_complete_master':True,'source_case_groups':cases,'source_panel_types':roles,'source_scope_issue':issue})
  assets.append({'id':ident,'kind':'schematic' if scheme else 'clinical_image','name':title,'local_path':local,'sha256':sha(raw),'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'modality':row['modality'],'source_context':context,'source':{'url':SOURCE,'license':{'name':row['license'],'url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','reviewed_at':'2026-10-10','evidence_path':'docs/endometriosis-source-review/published-source-preservation.json','attribution':credit}},'visual_review':{'status':'source_checked','sha256':sha(raw),'reviewed_at':'2026-10-10','evidence_path':'docs/endometriosis-source-review/published-source-preservation.json'},'anatomical_review':{'status':'pending','reason':limits}})
 proof={'pmcid':meta['pmcid'],'doi':meta['doi'],'title':meta['title'],'original_XML_sha256':sha(xml),'original_PDF_sha256':sha(pdf),'original_metadata_sha256':sha(meta_raw),'publisher_XML_PDF_MD5_verified':True,'permissions_xml':E.tostring(permissions,encoding='unicode'),'figures':records,'source_pixels_modified':False,'clinical_approval':False,'complete_reporting_anatomy_approved':False,'native_3D_geometry_supplied':False}
 save(out/'published-source-preservation.json',proof)
 for a in assets:a['source']['license']['evidence_sha256']=sha((out/'published-source-preservation.json').read_bytes())
 p=ROOT/'data/radiology/radiology-open-images.json';d=json.loads(p.read_text());d[INV]=rows;save(p,d)
 append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
 save(ROOT/'data/radiology/radiology-static-rasters.json',inventory())
 print('18 complete licensed source images: 5 clinical composites, 13 conceptual drawings; no every-structure approval.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
