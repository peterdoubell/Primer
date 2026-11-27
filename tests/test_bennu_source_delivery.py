"""Keep all three surveyed shapes outside the server function and usable from normal lesson links."""
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from primer.server import app

ROOT=Path(__file__).resolve().parents[1]
STATIC='web/reference-media/lesson-sources'
BASE='/source-media/reference-media/lesson-sources/bennu/'


def test_exact_native_inputs_are_in_the_static_build():
    config=json.loads((ROOT/'vercel.json').read_text())
    assert {'src':STATIC+'/**','use':'@vercel/static'} in config['builds']
    assert STATIC+'/**' in config['builds'][0]['config']['excludeFiles']
    assert any(rule.get('src')=='/source-media/(.*)' and rule.get('dest')=='/web/$1' for rule in config['routes'])
    source=json.loads((ROOT/'web/math/bennu-sections/source.json').read_text())
    models=source['models']
    assert [m['resolutionM'] for m in models]==[3.25,6.37,12.6]
    with TestClient(app) as client:
        for item in models:
            result=client.get(BASE+item['mesh'])
            assert result.status_code==200
            assert hashlib.sha256(result.content).hexdigest()==item['sha256']
        assert hashlib.sha256(client.get(BASE+'polycam.png').content).hexdigest()==source['photoSHA256']
        assert client.get(BASE+'unlisted-file').status_code==404
        registry=client.get('/app/activities/registry.json').json()
        for module in ('math.2.geometry','math.4.int-calc','math.5.numerical'):
            assert any(a['href']=='/app/math/bennu-sections/index.html' for a in registry[module])
