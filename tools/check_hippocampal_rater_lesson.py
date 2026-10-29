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
    data = ROOT / '.research/epilepsy-source-20261028/dryad-case10'
    proof_path = ROOT / 'docs/hippocampal-rater-review-20261028/lesson/proof.json'
    proof = json.loads(proof_path.read_bytes())
    mean = nib.load(data / 'anon_meansMT04294-0008-00001-000001-01_denoised_prinlm_b2.0.nii')
    primary = nib.load(data / 'Hippocampal_Segmentation.nii')
    second = nib.load(data / 'DICE_Hippocampal_Segmentation.nii')
    colors = np.array([[0,0,0],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[174,0,255],[190,112,38],[0,255,255]], dtype=float)
    pixels = 0
    for mount in proof['mounts']:
        for state in mount['states']:
            assert state['image'] == 'mean'
            for n, axis in enumerate([2,1,0]):
                selection = [slice(None)] * 3
                selection[axis] = state['ijk'][axis]
                a = np.asarray(primary.dataobj[tuple(selection)]).T[::-1]
                b = np.asarray(second.dataobj[tuple(selection)]).T[::-1]
                image = np.asarray(mean.dataobj[tuple(selection)], dtype=np.float64).T[::-1]
                gray = np.floor(255 * np.clip((image-state['low'])/(state['high']-state['low']),0,1)+.5)
                rgb = np.repeat(gray[:,:,None],3,axis=2)
                if state['mode'] == 'overlay':
                    labels = a if state['rater'] == 'primary' else b
                    hit = labels == state['code']
                    rgb[hit] = np.floor(.55*colors[state['code']] + .45*gray[hit,None] + .5)
                elif state['mode'] == 'difference':
                    for hit,color in [((a!=b)&(a>0)&(b>0),[255,160,0]),((a>0)&(b==0),[30,140,240]),((a==0)&(b>0),[235,80,190])]:
                        rgb[hit] = np.floor(.7*np.array(color)+.3*gray[hit,None]+.5)
                else:
                    raise ValueError('Unexpected hosted reader mode')
                rgba = np.concatenate([rgb.astype('uint8'),np.full((*gray.shape,1),255,dtype='uint8')],axis=2)
                assert hashlib.sha256(rgba.tobytes()).hexdigest() == state['pixelSHA256'][n]
                pixels += gray.size
    assert proof['browserChecksPassed']
    proof['allPassed'] = True
    proof['hostedPixelsComparedToOriginalNifti'] = pixels
    proof['hostedPixelComparisonPassed'] = True
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'hostedPixelComparisonPassed':True,'originalPixels':pixels}))


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
                child = subprocess.run(['node', str(ROOT / 'tools/check_hippocampal_rater_lesson.cjs')], input=json.dumps(fixture),
                                       cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
                sys.stdout.write(child.stdout)
                sys.stderr.write(child.stderr)
                if child.returncode == 0:
                    verify_hosted_pixels()
                if child.returncode:
                    raise RuntimeError('Hippocampal reader verification failed.')
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)

if __name__ == '__main__':
    main()
