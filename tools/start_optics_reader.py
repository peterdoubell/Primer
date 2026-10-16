"""Start a loopback reader with synthetic credentials/data for optics verification."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixture',type=Path,required=True,help='Private fixture JSON consumed by check_optics_reader.cjs')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
os.chdir(root)
sys.path.insert(0,str(root))
private=Path(tempfile.mkdtemp(prefix='primer-optics-synthetic-reader-'))
username='optics-synthetic-qa'
password=secrets.token_hex(24)
os.environ.update(PRIMER_DB=str(private/'record.db'),PRIMER_CONTENT_DIR=str(private/'content'),
                  PRIMER_BACKUP_DIR=str(private/'backups'),PRIMER_ACCESS_USERNAME=username,
                  PRIMER_ACCESS_PASSWORD=password,TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='')
os.environ.pop('VERCEL',None)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
args.fixture.parent.mkdir(parents=True,exist_ok=True)
args.fixture.write_text(json.dumps({'url':f'http://127.0.0.1:{port}','username':username,'password':password,
                                   'private_directory':str(private),'api_entrypoint':'api.index:app'},indent=2)+'\n')
args.fixture.chmod(0o600)
import uvicorn
uvicorn.run('api.index:app',host='127.0.0.1',port=port,log_level='warning')
