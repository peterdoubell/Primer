from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
import mimetypes
import sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from primer import cortical_contact_reference as contact,spl_limbic_reference as source
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  name=self.path.split('?',1)[0]
  try:
   if name.startswith(contact.PREFIX):
    asset=name[len(contact.PREFIX):];contact.references();file=contact.validate_file(asset)
   elif name.startswith(source.PREFIX):
    asset=name[len(source.PREFIX):]
    if asset not in ['coordinates.js','T1.bin.gz','T2.bin.gz','labels.bin.gz']:raise ValueError('Unrecognized test source')
    file=source.validate_file(asset)
   else:raise ValueError('Unrecognized test path')
   raw=file.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(file))[0]or'application/octet-stream');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
   if asset.endswith('.bin.gz'):self.send_header('Content-Encoding','gzip')
   self.end_headers();self.wfile.write(raw)
  except ValueError:self.send_error(404)
HTTPServer(('127.0.0.1',3990),Handler).serve_forever()
