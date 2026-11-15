"""Check the authenticated brain reader using isolated synthetic storage only."""
from pathlib import Path
import json,os,secrets,socket,subprocess,sys,tempfile,time,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
    env={k:v for k,v in os.environ.items() if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    with tempfile.TemporaryDirectory(prefix='primer-spl-reporting-reader-') as temporary:
        private=Path(temporary);fixture={'username':'synthetic-brain-reporting-qa','password':secrets.token_hex(24)}
        env.update(PRIMER_DB=str(private/'record.db'),PRIMER_CONTENT_DIR=str(private/'content'),PRIMER_BACKUP_DIR=str(private/'backups'),PRIMER_ACCESS_USERNAME=fixture['username'],PRIMER_ACCESS_PASSWORD=fixture['password'],TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='')
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        fixture['url']=f'http://127.0.0.1:{port}'
        fixture['mode']='preserve' if sys.argv[1:]==['--preservation-only'] else 'full'
        with (private/'server.log').open('w+') as log:
            server=subprocess.Popen([sys.executable,'-m','uvicorn','api.index:app','--host','127.0.0.1','--port',str(port),'--log-level','warning'],cwd=ROOT,env=env,stdout=log,stderr=log)
            try:
                for _ in range(120):
                    if server.poll() is not None:log.seek(0);raise RuntimeError('Synthetic reader server failed: '+log.read()[-2500:])
                    try:
                        with urllib.request.urlopen(fixture['url']+'/healthz',timeout=2) as response:
                            if response.status==200:break
                    except OSError:time.sleep(.25)
                else:raise RuntimeError('Synthetic reader did not become ready')
                result=subprocess.run(['node',str(ROOT/'tools/check_spl_reporting_reader.cjs')],input=json.dumps(fixture),text=True,cwd=ROOT,env=env,capture_output=True,timeout=600)
                sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
                if result.returncode:raise RuntimeError('SPL reporting reader check failed')
            finally:
                server.terminate()
                try:server.wait(timeout=10)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=10)
if __name__=='__main__':main()
