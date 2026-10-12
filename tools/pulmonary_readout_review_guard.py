"""Exact bounded readout amendment; reconstruct the immutable original reader."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='8444e3d0384bb9d0450ac414a52abd4bef61df851096de63004e37e531b02e04'
CURRENT='dcdd38c3eb1234b70c233b1cd739beaa9e6b4752c4576ee1671c6f4b2c8d3da5'
RECEIPT='a395263133ad7aa0cce10df829cd903eb940966bf14f99f5514298d072f78e5f'

def reconstruct_original_readout(body,receipt_body=None):
    current_hash=hashlib.sha256(body).hexdigest()
    if current_hash==ORIGINAL:return body
    if current_hash!=CURRENT:raise ValueError('Unreviewed pulmonary reader change')
    if receipt_body is None:receipt_body=(ROOT/'docs/pulmonary-nodule-independent-review-20261011/root-readout-provenance-repair-candidate.json').read_bytes()
    if hashlib.sha256(receipt_body).hexdigest()!=RECEIPT:raise ValueError('Unreviewed readout amendment record')
    r=json.loads(receipt_body)
    if r['file']!='web/anatomy/lidc-idri-0525/reference.js' or r['original_sha256']!=ORIGINAL or r['current_sha256']!=CURRENT or len(r['reversible_literal_blocks'])!=3:raise ValueError('Readout amendment scope differs')
    text=body.decode()
    for block in r['reversible_literal_blocks']:
        if block['occurrences']!=1 or text.count(block['current_literal'])!=1:raise ValueError('Readout literal scope differs')
        text=text.replace(block['current_literal'],block['original_literal'],1)
    original=text.encode()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL:raise ValueError('Readout amendment did not reconstruct exact original')
    return original
