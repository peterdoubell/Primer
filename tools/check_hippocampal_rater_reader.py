"""Local native-source reader check; no production account or learner writes."""
from pathlib import Path
import json,hashlib,threading,subprocess,sys,re,urllib.parse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import nibabel as nib,numpy as np
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'.research/epilepsy-source-20261028';O=D/'native-package';WEB=ROOT/'web/anatomy/dryad-hippocampal-case10';manifestRaw=(O/'manifest.json').read_bytes();m=json.loads(manifestRaw);sha=lambda b:hashlib.sha256(b).hexdigest();images={k:nib.load(D/'dryad-case10'/v['sourceFile'])for k,v in m['volumes'].items()};payloads=set(m['packs'])|{r['file']for r in m['meshes'].values()};colours=np.array([[0,0,0],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[174,0,255],[190,112,38],[0,255,255]],float)
acquisitionPath=D/'dryad-case10-acquisition.json'
assert sha(acquisitionPath.read_bytes())=='dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'
for sourceRow in json.loads(acquisitionPath.read_bytes())['files']:assert sha((D/sourceRow['file']).read_bytes())==sourceRow['sha256']
packageProof=json.loads((D/'native-package-independent-proof.json').read_bytes());assert packageProof['allPassed'] and packageProof['manifestSHA256']==sha(manifestRaw)
assert packageProof['archiveSourceAuthenticationPending']==m['fullArchiveVerificationPending']
if not m['fullArchiveVerificationPending']:
 receipt=(D/'dryad-stream-verification.json').read_bytes();auth=json.loads(receipt);assert sha(receipt)==m['sourceArchiveAuthentication']['verificationReceiptSHA256'] and auth['matchesPublisherSHA256'] is True and auth['sha256']=='e76586274bba73f64f2355b093da3ae671fb8e77bb62c13528cfac9d4893ba2e'
def pixels(q):
 axis=q['axis'];idx=q['ijk'][axis];selection=[slice(None)]*3;selection[axis]=idx
 a=np.asarray(images['primary'].dataobj[tuple(selection)]).T[::-1];b=np.asarray(images['second'].dataobj[tuple(selection)]).T[::-1];labels=a if q['rater']=='primary'else b
 if q['mode']=='schematic':gray=np.where(labels>0,90,15)
 else:
  values=np.asarray(images[q['image']].dataobj[tuple(selection)],dtype=np.float64).T[::-1];gray=np.floor(255*np.clip((values-q['low'])/(q['high']-q['low']),0,1)+.5)
 rgb=np.repeat(gray[:,:,None],3,axis=2).astype(float)
 if q['mode']in ['overlay','schematic']:
  hit=labels==q['code'];rgb[hit]=np.floor(.55*colours[q['code']]+.45*gray[hit,None]+.5)
 if q['mode']=='difference':
  for hit,c in [((a!=b)&(a>0)&(b>0),[255,160,0]),((a>0)&(b==0),[30,140,240]),((a==0)&(b>0),[235,80,190])]:rgb[hit]=np.floor(.7*np.array(c)+.3*gray[hit,None]+.5)
 rgba=np.concatenate([rgb.astype('uint8'),np.full((*gray.shape,1),255,dtype='uint8')],axis=2);(D/f'debug-expected-{axis}.bin').write_bytes(rgba.tobytes());return sha(rgba.tobytes())
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def respond(self,raw,content,status=200,extra={}):
  self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
  for k,v in extra.items():self.send_header(k,v)
  self.end_headers()
  try:self.wfile.write(raw)
  except(BrokenPipeError,ConnectionResetError):pass
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  if path=='/config.json':return self.respond(json.dumps({'manifestSHA256':sha(manifestRaw),'blobPrefix':'/payload/'}).encode(),'application/json')
  if path=='/manifest.json':return self.respond(manifestRaw,'application/json')
  if path.startswith('/payload/')and path[9:]in payloads:
   file=O/path[9:];size=file.stat().st_size;r=self.headers.get('Range')
   if r:
    match=re.fullmatch(r'bytes=(\d+)-(\d+)',r)
    if not match:return self.send_error(416)
    start,end=map(int,match.groups())
    if not 0<=start<=end<size:return self.send_error(416)
    with file.open('rb')as f:f.seek(start);raw=f.read(end-start+1)
    return self.respond(raw,'application/octet-stream',206,{'Content-Range':f'bytes {start}-{end}/{size}'})
   return self.respond(file.read_bytes(),'application/octet-stream')
  name='index.html'if path=='/'else path[1:]
  if name in ['index.html','viewer.js','transport.js','viewer.css']:return self.respond((WEB/name).read_bytes(),{'html':'text/html','js':'text/javascript','css':'text/css'}[name.split('.')[-1]])
  return self.send_error(404)
 def do_POST(self):
  if self.path!='/oracle':return self.send_error(404)
  length=int(self.headers.get('Content-Length','0'))
  if not 0<length<16000:return self.send_error(400)
  q=json.loads(self.rfile.read(length));codes=nib.aff2axcodes(images[q['image']].affine);opposite={'R':'L','L':'R','A':'P','P':'A','S':'I','I':'S'};edges=[]
  for axis in [2,1,0]:
   u,v=[i for i in range(3)if i!=axis];edges.append([opposite[codes[u]],codes[u],codes[v],opposite[codes[v]]])
  result={'pixelSHA256':[pixels(dict(q,axis=a))for a in [2,1,0]],'orientation':edges,'probe':{'primary':int(images['primary'].dataobj[tuple(q['ijk'])])if q['image']=='mean'else None,'second':int(images['second'].dataobj[tuple(q['ijk'])])if q['image']=='mean'else None,'intensity':None if q['mode']=='schematic'else float(images[q['image']].dataobj[tuple(q['ijk'])])}};key=q['rater']+':'+str(q['code'])
  if q['image']=='mean' and key in m['meshes']:
   z=np.load(D/'case10-boundaries'/f"{q['rater']}-{q['code']}.npz");result['positionsSHA256']=sha(z['world'].astype('<f4').tobytes());result['indicesSHA256']=sha(z['triangles'].astype('<u4').tobytes())
  return self.respond(json.dumps(result).encode(),'application/json')
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 if sys.argv[1:] not in [[],['--adverse']]:raise ValueError('Only --adverse is supported')
 script='check_hippocampal_rater_adverse.cjs'if sys.argv[1:]else'check_hippocampal_rater_reader.cjs'
 result=subprocess.run(['node',str(ROOT/'tools'/script)],input=json.dumps({'url':f'http://127.0.0.1:{server.server_port}'}),text=True,cwd=ROOT);sys.exit(result.returncode)
finally:server.shutdown();server.server_close()
