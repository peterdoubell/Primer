"""Exact offline pulmonary-to-main views; no runtime or approval waiver."""
from pathlib import Path
import hashlib
import json
from tools.anatomy_sources.pulmonary_ui_compatibility import restore_previous_app
from tools.number_theory_runtime_compatibility import pulmonary_product_bytes
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/pulmonary-release-integration-review-20261012/main-runtime-inverse.json'
PROOF_SHA256='19c0fc4f13c74792a0447b9fb076253fecd66c6020502ffb4fe8fed74830446d'
PINS={'primer/server.py': ('8c0071159fa528ce1b5453d18dc2357663e349b0edf02dd6a54a42c90723a906', 'b90ad60a33233321a0151ab454276018001e8a4496b6bc23861b9321adc3ce45'), 'primer/module_media.py': ('078861258791477395df54b3b1135a121187a47379416141d54d258f12ceb1f1', '5876b7a8e0ce3a42f44bfc408dab37c1f790170bd9e0d56a98c6d183901bb2d7'), 'web/lesson-models.js': ('2ac415278e51eb56cbc183e97f67f2371ad66082177a7a0fd79efc988c251c50', '1fe0aa5426059fbddf0c75988bb88305d6f04ba5b03222ecaff99a354e6f0b98'), 'primer/source_native_inspectors.py': ('03c3f43f6995391b182e0b4b7b8ae947f10dbe9d2fe83b699a8b12662f8b6a09', 'cf3086ae256ded8ee5443db8569ae53c7c0f9e75983fe675c70718a1fb5bc252')}

def restore_main_runtime_bytes(relative, raw):
    from tools.physics_wave_runtime_compatibility import before_wave_bytes
    raw=before_wave_bytes(relative,raw,allow_older=True)
    if relative in PINS and hashlib.sha256(raw).hexdigest()==PINS[relative][0]:
        return raw
    raw=pulmonary_product_bytes(relative,raw)
    if relative=='web/app.js':
        if hashlib.sha256(raw).hexdigest()=='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0':
            return raw
        return restore_previous_app(raw.decode()).encode()
    if relative not in PINS:
        return raw
    before,current=PINS[relative]
    digest=hashlib.sha256(raw).hexdigest()
    if digest==before:
        return raw
    if digest!=current:
        raise ValueError('Unreviewed pulmonary runtime byte change')
    proof=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(proof).hexdigest()!=PROOF_SHA256:
        raise ValueError('Pulmonary exact inverse evidence changed')
    row=json.loads(proof)['files'][relative]
    if (row['main_sha256'],row['current_sha256'])!=(before,current):
        raise ValueError('Pulmonary exact inverse leaves its fixed file scope')
    text=raw.decode()
    for change in row['changes']:
        if text.count(change['after'])!=1:
            raise ValueError('Pulmonary exact inverse lacks unique changed block')
        text=text.replace(change['after'],change['before'],1)
    restored=text.encode()
    if hashlib.sha256(restored).hexdigest()!=before:
        raise ValueError('Pulmonary exact inverse changes unrelated source bytes')
    return restored
