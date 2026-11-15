"""Run the actual reader proof against isolated synthetic loopback data only.

No command-line path is opened. Fixture credentials go to the child on stdin;
proofs have fixed repository destinations. The server is terminated on exit.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def verify_hosted_pixels():
    import hashlib
    import nibabel as nib
    import numpy as np
    source=ROOT/'.research/fcd-source-20261028'
    manifest=json.loads((ROOT/'web/anatomy/bonn-fcd-case4/manifest.json').read_bytes())
    def load(role):
        row=manifest['volumes'][role];path=source/row['sourceFile']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sourceSHA256']
        return np.asarray(nib.load(path).dataobj)
    image,mask=load('flair'),load('roi')
    target=ROOT/'docs/fcd-native-source-review-20261028/lesson/proof.json'
    proof=json.loads(target.read_bytes());pixels=0
    for mount in proof['mounts']:
        for state in mount['states']:
            assert state['ijk']==[71,177,148]
            for axis in range(3):
                selection=[slice(None)]*3;selection[axis]=state['ijk'][axis]
                grey=np.floor(255*np.clip((image[tuple(selection)]-state['low'])/(state['high']-state['low']),0,1)+.5)
                hit=mask[tuple(selection)]==1;rgb=np.repeat(grey[:,:,None],3,axis=2)
                if state['mode']=='overlay':rgb[hit]=np.floor(.55*rgb[hit]+.45*np.array([255,100,20])+.5)
                elif state['mode']=='mask':rgb[:]=0;rgb[hit]=[255,100,20]
                else:assert state['mode']=='mri'
                rgba=np.empty((*grey.shape,4),np.uint8);rgba[:,:,:3]=rgb;rgba[:,:,3]=255
                assert hashlib.sha256(rgba.transpose(1,0,2)[::-1].copy().tobytes()).hexdigest()==state['pixelSHA256'][axis]
                pixels+=grey.size
    assert proof['browserChecksPassed']
    proof.update(allPassed=True,hostedPixelsComparedToOriginalNifti=pixels,hostedPixelComparisonPassed=True)
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'allPassed':True,'sourcePixels':pixels}))


def main():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))}
    with tempfile.TemporaryDirectory(prefix='primer-hippocampal-rater-synthetic-') as temporary:
        private = Path(temporary)
        fixture = {'username': 'hippocampal-rater-synthetic-qa', 'password': secrets.token_hex(24)}
        env.update(PRIMER_DB=str(private / 'record.db'), PRIMER_CONTENT_DIR=str(private / 'content'),
                   PRIMER_BACKUP_DIR=str(private / 'backups'), PRIMER_ACCESS_USERNAME=fixture['username'],
                   PRIMER_ACCESS_PASSWORD=fixture['password'], TURSO_DATABASE_URL='', TURSO_AUTH_TOKEN='')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        fixture['url'] = f'http://127.0.0.1:{port}'
        with (private / 'server.log').open('w+') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'api.index:app', '--host', '127.0.0.1',
                                       '--port', str(port), '--log-level', 'warning'], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                # Local source inventories hash the full native assets on first
                # access. Allow cold filesystem reads without skipping health.
                deadline = time.monotonic() + 900
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        raise RuntimeError('Synthetic server exited before readiness.')
                    try:
                        with urllib.request.urlopen(fixture['url'] + '/healthz', timeout=30) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.25)
                else:
                    raise RuntimeError('Synthetic server did not become ready.')
                child = subprocess.run(['node', str(ROOT / 'tools/check_bonn_fcd_lesson.cjs')], input=json.dumps(fixture),
                                       cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
                sys.stdout.write(child.stdout)
                sys.stderr.write(child.stderr)
                if child.returncode == 0:
                    verify_hosted_pixels()
                if child.returncode:
                    raise RuntimeError('FCD reader verification failed.')
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)

if __name__ == '__main__':
    main()
