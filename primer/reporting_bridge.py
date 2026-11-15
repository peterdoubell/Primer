"""Server-only bridge to the reporting service; never expose its key to JavaScript."""
import copy
from functools import lru_cache
import json
import gzip
import os
from pathlib import Path
import httpx
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

router=APIRouter(prefix='/api/radiology/reporting')

SERVICE_URLS = {
    'https://radiology-reporting-api.vercel.app': 'https://radiology-reporting-api.vercel.app',
    'http://127.0.0.1:8770': 'http://127.0.0.1:8770',
    'http://localhost:8770': 'http://localhost:8770',
}

CALCULATOR_PATHS = {
    'acr_tirads_2017': 'calculators/acr_tirads_2017',
    'pirads_v2_1': 'calculators/pirads_v2_1',
    'cadrads_2_0': 'calculators/cadrads_2_0',
    'prostate_volume_psad': 'calculators/prostate_volume_psad',
    'orads_us_2022': 'calculators/orads_us_2022',
    'lirads_ct_mri_2018': 'calculators/lirads_ct_mri_2018',
    'recist_1_1': 'calculators/recist_1_1',
    'lesion_growth': 'calculators/lesion_growth',
}


@lru_cache(maxsize=1)
def structured_forms():
    path = Path(__file__).resolve().parents[1] / 'data/radiology/structured-reporting.json'
    return json.loads(path.read_text()) if path.exists() else {'forms': {}}


@lru_cache(maxsize=1)
def descriptor_forms():
    path = Path(__file__).resolve().parents[1] / 'data/radiology/descriptor-reporting.json'
    packed = path.with_suffix('.json.gz')
    return json.loads(gzip.decompress(packed.read_bytes()) if packed.exists() else path.read_text())


def descriptor_variant(identifier):
    for form in descriptor_forms()['forms'].values():
        for investigation in form['investigations']:
            if investigation['id'] == identifier and (investigation.get('base_investigation_id') or investigation.get('kind') == 'source-worksheet'):
                return dict(investigation, guide_id=form['guide_id'])
    return None


def with_descriptor_investigations(index):
    """Add reporting-only examinations without rewriting teaching references."""
    modules = list(index['modules'])
    known = {item['id']:item for item in modules}
    for form in descriptor_forms()['forms'].values():
        for investigation in form['investigations']:
            base = known.get(investigation.get('base_investigation_id'))
            if investigation['id'] in known:
                continue
            if not base and investigation.get('kind') == 'source-worksheet':
                base = {'section':'Reporting worksheets','topic':form['title'],
                        'modality':investigation.get('modality') or 'Reference'}
            if not base:
                continue
            sources = investigation.get('sources', [])
            modules.append(dict(base, id=investigation['id'], module_id=form['guide_id'],
                title=investigation['title'], modality=investigation.get('modality') or 'Reference',
                summary='Structure-by-structure selectable reporting.',
                source_titles=[source['title'] for source in sources],
                topics=[base['topic'],investigation.get('modality') or 'Reference','structured report'],
                image_count=0,motion_count=0,template_count=1,classification='',staging_systems=[],
                step_count=len(investigation['sections']),reviewed_at=investigation['content_revision']))
    return dict(index,modules=modules,count=len(modules))


def descriptor_variant_detail(investigation, regional):
    """A reporting-only view: do not relabel radiographs or lessons as MRI."""
    regional = regional or {'section':'Reporting worksheets','topic':investigation['title'],'family':'reference'}
    groups = list(dict.fromkeys(section['group'] for section in investigation['sections']))
    sources = investigation['sources']
    template_id = 'anatomic-' + investigation['id']
    sections = [{'heading':group.upper(),'body':'\n'.join(section['label'] + ': select the observed findings.'
                 for section in investigation['sections'] if section['group'] == group)} for group in groups]
    steps = [{'label':section['label'],'detail':'Assess the individual structure.',
              'sections':[section['group'].upper()],
              'normal':{section['group'].upper():section['normal']['text']} if section['normal'] else {},
              'findings':[finding['text'] for finding in section['findings']], 'images':[], 'measurements':[]}
             for section in investigation['sections']]
    reporting = {'title':investigation['title'],'reviewed_at':investigation['content_revision'],
                 'protocol':[],'checklist':[{'label':step['label'],'detail':step['detail'],'sections':step['sections']} for step in steps],
                 'measurements':[],'classification':None,'template_sections':sections,
                 'pitfalls':[],'escalation':[],'impression_prompts':[],'sources':sources}
    ref = {'descriptor_only':True,'overview':'Anatomical reporting checklist.',
           'reviewed_at':investigation['content_revision'],'reporting':reporting,
           'report_templates':[{'id':template_id,'title':investigation['title'],'sections':sections,'sources':sources}],
           'walkthrough':{'template_id':template_id,'reviewed_at':investigation['content_revision'],
                          'start':{'sections':[],'images':[]},'steps':steps,'finish':{'sections':[],'images':[]}},
           'reading':[],'key_images':[],'structure_atlas':[],
           'spatial_model':{'family':regional.get('family','joint')}}
    return {'id':investigation['id'],'module_id':investigation['guide_id'],
            'title':investigation['title'],'section':regional['section'],'topic':regional['topic'],
            'modality':investigation.get('modality') or 'Reference','source_titles':[source['title'] for source in sources],
            'goal':'Structure-by-structure selectable reporting.','radiology_reference':ref,'lesson_media':[]}


def with_structured_form(detail):
    """Attach reporting controls to a response, preserving canonical lesson data."""
    catalogue = structured_forms()
    form = catalogue['forms'].get(detail.get('module_id'))
    if form is None:
        return detail
    result = dict(detail)
    result['radiology_reference'] = dict(detail['radiology_reference'])
    result['radiology_reference']['structured_form'] = copy.deepcopy(form)
    result['radiology_reference']['structured_form']['form_version'] = catalogue.get('schema_hash', catalogue.get('version'))
    descriptors = descriptor_forms()
    descriptor = copy.deepcopy(descriptors['forms'][detail['module_id']])
    descriptor['version'] = descriptor['schema_hash']
    descriptor['selected_investigation_id'] = detail['id']
    result['radiology_reference']['structured_form'].update({
        'descriptor_form': descriptor,
        'calculator_ids': descriptor['calculator_ids'],
        'descriptor_version': descriptor['schema_hash'],
        'snapshot_id': descriptors['source_snapshot_id'],
    })
    selected = next((item for item in descriptor['investigations'] if item['id'] == detail['id']), None)
    if selected and selected.get('presentation') == 'anatomic_rows':
        reporting = dict(result['radiology_reference'].get('reporting', {}))
        sources = list(reporting.get('sources', []))
        known = {source['url'] for source in sources}
        sources.extend(source for source in selected.get('sources', []) if source['url'] not in known)
        reporting['sources'] = sources
        result['radiology_reference']['reporting'] = reporting
    return result

def configuration():
    configured=os.getenv('REPORTING_SERVICE_URL','https://radiology-reporting-api.vercel.app').rstrip('/')
    url=SERVICE_URLS.get(configured)
    if url is None:raise ValueError('Reporting service origin is not approved.')
    key=os.getenv('REPORTING_API_KEY','')
    if not key and not os.getenv('VERCEL'):
        local=Path.home()/'.config/primer-reporting/production.env'
        if local.is_file():
            for line in local.read_text().splitlines():
                if line.startswith('REPORTING_API_KEY='):key=line.split('=',1)[1]
    if not key:raise ValueError('Reporting service key is not configured on this server.')
    return url,key

async def forward(path,payload=None):
    try:
        base,key=configuration()
        if payload is not None and len(json.dumps(payload).encode())>100000:return JSONResponse({'error':{'code':'body_too_large'}},status_code=413)
        async with httpx.AsyncClient(timeout=15,follow_redirects=False) as client:
            response=await client.request('POST' if payload is not None else 'GET',base+'/v1/'+path,headers={'Authorization':'Bearer '+key},json=payload if payload is not None else None)
        if response.status_code not in (200,400,404,409,422):return JSONResponse({'error':{'code':'reporting_service_unavailable'}},status_code=503)
        return JSONResponse(response.json(),status_code=response.status_code,headers={'Cache-Control':'no-store'})
    except Exception:
        return JSONResponse({'error':{'code':'reporting_service_unavailable','message':'The reporting service is unavailable or has not been configured.'}},status_code=503)

@router.get('/calculators/{calculator_id}')
async def calculator(calculator_id:str):
    path = CALCULATOR_PATHS.get(calculator_id)
    if path is None:return JSONResponse({'error':{'code':'unknown_calculator'}},status_code=404)
    return await forward(path)

@router.post('/calculators/{calculator_id}/calculate')
async def calculate(calculator_id:str,payload:dict=Body(...)):
    path = CALCULATOR_PATHS.get(calculator_id)
    if path is None:return JSONResponse({'error':{'code':'unknown_calculator'}},status_code=404)
    return await forward(path+'/calculate',payload)


@router.post('/reports/structured')
async def render_descriptor_report(payload:dict=Body(...)):
    return await forward('reports/structured',payload)
