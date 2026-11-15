#!/usr/bin/env python3
"""One task-owned loopback socket and isolated synthetic database; no inherited cloud auth."""
import json
import os
import socket
import tempfile
from pathlib import Path

# Clear runtime backend/auth configuration before importing the server.
for key in list(os.environ):
    if key.startswith(('PRIMER_', 'TURSO_', 'GOOGLE_', 'VERCEL_')):
        del os.environ[key]
qa_dir = Path(tempfile.mkdtemp(prefix='primer-number-theory-qa-'))
os.environ['PRIMER_DB'] = str(qa_dir/'reader.db')
os.environ['PRIMER_BACKUP_DIR'] = str(qa_dir/'backups')
import uvicorn
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('127.0.0.1', 0))
sock.listen(128)
port = sock.getsockname()[1]
receipt = {'task':'number-theory', 'pid':os.getpid(), 'port':port, 'url':f'http://127.0.0.1:{port}', 'db':os.environ['PRIMER_DB'], 'directory':str(qa_dir), 'isolated':True}
(qa_dir/'server-started.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('NUMBER_THEORY_SERVER='+json.dumps(receipt), flush=True)
interrupted = False
returned = False
try:
    uvicorn.Server(uvicorn.Config('primer.server:app', log_level='warning', lifespan='on')).run(sockets=[sock])
    returned = True
except KeyboardInterrupt:
    interrupted = True
finally:
    sock.close()
    (qa_dir/'server-closed.json').write_text(json.dumps({**receipt, 'socketClosed':sock.fileno()==-1, 'serverRunReturnedNormally':returned, 'interrupted':interrupted}, indent=2)+'\n')
    print('NUMBER_THEORY_SERVER_CLOSED='+str(qa_dir/'server-closed.json'), flush=True)
