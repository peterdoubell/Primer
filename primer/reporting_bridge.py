"""Server-only bridge to the reporting service; never expose its key to JavaScript."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

router=APIRouter(prefix='/api/radiology/reporting')

def configuration():
    url=os.getenv('REPORTING_SERVICE_URL','https://radiology-reporting-api.vercel.app').rstrip('/')
    key=os.getenv('REPORTING_API_KEY','')
    if not key and not os.getenv('VERCEL'):
        local=Path.home()/'.config/primer-reporting/production.env'
        if local.is_file():
            for line in local.read_text().splitlines():
                if line.startswith('REPORTING_API_KEY='):key=line.split('=',1)[1]
    parsed=urlsplit(url)
    if parsed.scheme!='https' and not(parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost')):raise ValueError('Reporting service requires HTTPS or loopback.')
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
    if calculator_id not in {'acr_tirads_2017','pirads_v2_1','cadrads_2_0','prostate_volume_psad'}:return JSONResponse({'error':{'code':'unknown_calculator'}},status_code=404)
    return await forward('calculators/'+calculator_id)

@router.post('/calculators/{calculator_id}/calculate')
async def calculate(calculator_id:str,payload:dict=Body(...)):
    if calculator_id not in {'acr_tirads_2017','pirads_v2_1','cadrads_2_0','prostate_volume_psad'}:return JSONResponse({'error':{'code':'unknown_calculator'}},status_code=404)
    return await forward('calculators/'+calculator_id+'/calculate',payload)
