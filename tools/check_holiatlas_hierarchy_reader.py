"""Exercise the real authenticated atlas reader using isolated synthetic storage."""
from pathlib import Path
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = {k: v for k, v in os.environ.items() if not k.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))}
    with tempfile.TemporaryDirectory(prefix='primer-holiatlas-hierarchy-') as temporary:
        private = Path(temporary)
        fixture = {'username': 'synthetic-holiatlas-hierarchy-qa', 'password': secrets.token_hex(24)}
        env.update(PRIMER_DB=str(private / 'record.db'), PRIMER_CONTENT_DIR=str(private / 'content'), PRIMER_BACKUP_DIR=str(private / 'backups'), PRIMER_ACCESS_USERNAME=fixture['username'], PRIMER_ACCESS_PASSWORD=fixture['password'], TURSO_DATABASE_URL='', TURSO_AUTH_TOKEN='')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        fixture['url'] = f'http://127.0.0.1:{port}'
        with (private / 'server.log').open('w+') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'api.index:app', '--host', '127.0.0.1', '--port', str(port), '--log-level', 'warning'], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                for _ in range(480):
                    if server.poll() is not None:
                        log.seek(0)
                        raise RuntimeError('Synthetic hierarchy server failed: ' + log.read()[-2500:])
                    try:
                        with urllib.request.urlopen(fixture['url'] + '/healthz', timeout=2) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.25)
                else:
                    raise RuntimeError('Synthetic hierarchy server did not become ready')
                result = subprocess.run(['node', str(ROOT / 'tools/check_holiatlas_hierarchy_reader.cjs')], input=json.dumps(fixture), text=True, cwd=ROOT, env=env, timeout=3600)
                if result.returncode:
                    raise RuntimeError('Authenticated hierarchy reader check failed')
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)


if __name__ == '__main__':
    main()
