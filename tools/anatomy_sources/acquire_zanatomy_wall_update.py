#!/usr/bin/env python3
"""Acquire the reviewed current scene and official reader inputs without installation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

COMMIT='ded1a55381328f3f242426f0e8e711c5fca62c14'
ARCHIVE_SHA='e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736'
SCENE_SHA='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
RUNTIME='blender-4.2.23-macos-arm64.dmg'


def fetch(url,path):
    if not path.exists():subprocess.run(['curl','--fail','--location','--max-time','120','--silent','--show-error',url,'-o',str(path)],check=True)


def acquire(root):
    root.mkdir(parents=True,exist_ok=True)
    for endpoint,file in [(f'repos/Z-Anatomy/Models-of-human-anatomy/contents/Z-Anatomy.zip?ref={COMMIT}','archive-metadata.json'),
                          (f'repos/Z-Anatomy/Models-of-human-anatomy/commits/{COMMIT}','commit.json')]:
        with (root/file).open('w') as stream:subprocess.run(['gh','api',endpoint],stdout=stream,check=True)
    base='https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/'+COMMIT+'/'
    for name in ['Z-Anatomy.zip','License.txt']:fetch(base+name,root/name)
    raw=(root/'Z-Anatomy.zip').read_bytes();meta=json.loads((root/'archive-metadata.json').read_text())
    if len(raw)!=86734957 or hashlib.sha256(raw).hexdigest()!=ARCHIVE_SHA or hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()!=meta['sha']:raise ValueError('Pinned original archive differs')
    with zipfile.ZipFile(root/'Z-Anatomy.zip') as z:
        if z.testzip() is not None:raise ValueError('Archive CRC differs')
        scene=z.read('Z-Anatomy/Startup.blend')
        if len(scene)!=306838281 or hashlib.sha256(scene).hexdigest()!=SCENE_SHA:raise ValueError('Original scene differs')
        (root/'Startup.blend').write_bytes(scene)
    url='https://download.blender.org/release/Blender4.2/'+RUNTIME
    (root/'runtime-selection.json').write_text(json.dumps({'file':RUNTIME,'url':url},indent=2)+'\n')
    sums=RUNTIME.replace('-macos-arm64.dmg','.sha256')
    fetch(url,root/RUNTIME);fetch('https://download.blender.org/release/Blender4.2/'+sums,root/sums)
    match=re.search(r'([0-9a-f]{64})\s+\*?'+re.escape(RUNTIME),(root/sums).read_text())
    if match is None or hashlib.sha256((root/RUNTIME).read_bytes()).hexdigest()!=match[1]:raise ValueError('Official reader checksum differs')
    print('Pinned scene and official reader verified in ignored staging; no application installed.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
