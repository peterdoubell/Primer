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

def main():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))}
    with tempfile.TemporaryDirectory(prefix='primer-geometry-measures-synthetic-') as temporary:
        private = Path(temporary)
        fixture = {'username': 'geometry-measures-synthetic-qa', 'password': secrets.token_hex(24)}
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
                child = subprocess.run(['node', str(ROOT / 'tools/check_geometry_measures_lesson.cjs')], input=json.dumps(fixture),
                                       cwd=ROOT, env=env, text=True, capture_output=True, timeout=1200)
                sys.stdout.write(child.stdout)
                sys.stderr.write(child.stderr)
                if child.returncode:
                    raise RuntimeError('Coordinate plane reader verification failed.')
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)

if __name__ == '__main__':
    main()
