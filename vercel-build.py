"""Copy immutable public source media to the CDN, retaining runtime evidence files."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
ATLAS_DIRS = ('bodyparts3d', 'msk-atlas', 'msk-cervical', 'msk-mri-knee', 'msk-mri-ankle')


def build():
    sources = [p for atlas in ATLAS_DIRS for p in (ROOT/'web/anatomy'/atlas).rglob('*')
               if p.is_file() and (p.name.endswith('.bin') or p.name.endswith('.bin.gz'))]
    sources.append(ROOT/'web/reference-media/prenatal-development/prenatal-development.gif')
    for source in sources:
        target = ROOT/'public/source-media'/source.relative_to(ROOT/'web')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    print(f'Copied {len(sources)} source media files to static hosting, without altering bytes.')


if __name__ == '__main__':
    build()
