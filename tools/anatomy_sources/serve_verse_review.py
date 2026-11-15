"""Serve only the local VerSe review package, with gzip mesh transport headers."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]/'output/msk-verse521'


class ReviewHandler(SimpleHTTPRequestHandler):
    def guess_type(self,path):
        return 'application/octet-stream' if path.endswith('.bin.gz') else super().guess_type(path)

    def end_headers(self):
        if urlsplit(self.path).path.endswith('.bin.gz'):
            self.send_header('Content-Encoding','gzip')
        super().end_headers()


if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',8826),partial(ReviewHandler,directory=str(ROOT))).serve_forever()
