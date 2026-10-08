"""Verify original motion bytes locally or exact release-checked static contracts."""
import hashlib,json,os
from pathlib import Path
from .source_motion_contract import parse_motion_contract
PREFIX='/app/reference-media/radiology-motion/'
def verified_motion_contract(path,src,digest,data_dir):
    path=Path(path)
    if path.is_file():
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Motion file changed')
        return parse_motion_contract(raw)
    if not os.environ.get('VERCEL') or not src.startswith(PREFIX):raise ValueError('Motion file missing')
    inventory=json.loads((Path(data_dir)/'radiology-static-motion.json').read_text())
    if inventory.get('schema_version')!=1:raise ValueError('Invalid static motion inventory')
    row=inventory['files'].get(src)
    if not isinstance(row,dict) or row.get('sha256')!=digest or type(row.get('bytes')) is not int or row['bytes']<24 or not isinstance(row.get('contract'),dict):raise ValueError('Hosted motion metadata differs from verified release')
    return row['contract']
