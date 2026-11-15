import os,json,tempfile,socket,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];os.chdir(root);sys.path.insert(0,str(root))
private=Path(tempfile.mkdtemp(prefix='primer-pulmonary-hosted-reader-'))
os.environ.update(PRIMER_DB=str(private/'record.db'),PRIMER_CONTENT_DIR=str(private/'content'),PRIMER_BACKUP_DIR=str(private/'backups'),PRIMER_ACCESS_USERNAME='pulmonary-release-reader',PRIMER_ACCESS_PASSWORD='source-qa-only',TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='')
os.environ['VERCEL']='1'
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
fixture={'url':'https://127.0.0.1:'+str(port),'username':'pulmonary-release-reader','password':'source-qa-only','private_directory':str(private),'api_entrypoint':'api.index:app','pid':os.getpid(), 'TLS':True}
p=Path(__file__).with_name('fixture.json');p.write_text(json.dumps(fixture,indent=2)+'\n');p.chmod(0o600)
import uvicorn
from api.index import app as book
from starlette.responses import FileResponse
cdn={}
for width in (800,1600):
 relative='illustrations/forest/radiology/rad-4-pulmonary-nodule-'+str(width)+'.webp'
 cdn['/source-media/'+relative]=root/'web'/relative
config=json.loads((root/'vercel.json').read_text())
assert {'src':'/source-media/(.*)','dest':'/web/$1'} in config['routes']
assert {'src':'web/illustrations/**/*.webp','use':'@vercel/static'} in config['builds']
async def fixture_app(scope,receive,send):
 if scope['type']=='http' and scope['path'] in cdn and scope['method'] in ('GET','HEAD'):
  await FileResponse(cdn[scope['path']],media_type='image/webp')(scope,receive,send)
 else: await book(scope,receive,send)
uvicorn.run(fixture_app,host='127.0.0.1',port=port,log_level='warning',ssl_keyfile=str(Path(__file__).with_name('key.pem')),ssl_certfile=str(Path(__file__).with_name('cert.pem')))
