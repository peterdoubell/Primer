"""Server-only bridge to the reporting service; never expose its key to JavaScript."""
import copy
from functools import lru_cache
import json
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
}


@lru_cache(maxsize=1)
def structured_forms():
    path = Path(__file__).resolve().parents[1] / 'data/radiology/structured-reporting.json'
    return json.loads(path.read_text()) if path.exists() else {'forms': {}}


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
