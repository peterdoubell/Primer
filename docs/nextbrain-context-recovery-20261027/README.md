# NextBrain WebGL context recovery

The deployed PR180 viewer could finish an old mesh decompression after a WebGL context had been lost and restored. Its generation checks prevented that old mesh from replacing the current selection, but cleanup still passed the invalidated buffers to the restored context. That produced `GL_INVALID_OPERATION` (1282); the next camera draw raised `3D draw failed`.

The fix assigns each allocated mesh a context epoch, advances the epoch on context loss, and skips cleanup of buffers from an invalidated or currently lost context. It retains the existing GL error checks. No image, mask, geometry, manifest, coordinate, or clinical-approval change is asserted by this repair.

`before-proof.json` records the failure against the exact viewer from deployed merge `e2d2003d22f0e8516d9066ab15fc9ac5346c795d`. `viewer.before.js.txt` preserves those bytes. `baseline-git-proof.json` supplies the raw Git commit and four tree objects along the viewer path; CI can verify the commit/tree/blob hash chain even in a shallow checkout.

`after-proof.json` records the same adversarial sequence against the current viewer: start at code19, select code29, hold six plane decoders and the first mesh decoder, lose and restore the GL context, wait for the replacement mesh, then release the old decoders and rotate. There are no page errors, GL errors, or stale buffer deletions. All five actual restored code29 GPU chunks match the source manifest, covering13,959,144 bytes. The observer wrappers record API calls and return GL errors unchanged; they do not clear or suppress the fault.

The before proof's individual case has `passed: true` because selection/readiness and a subsequent error query succeeded. That does **not** mean recovery passed: the failing draw had already consumed the sticky GL error and thrown. The top-level failure, recorded1282, stale deletions and page error are the authoritative negative result.

This is a controlled Chromium/software-WebGL2 recovery regression at390px width. It does not replace the earlier source-data,98-region geometry, pixel, anatomy or clinical reviews. Those remain historical evidence for their original scope. CI validates these captured observations and their exact source identities; it does not execute a browser or download the large source packet.

## Reproduce locally

Run from the repository root with Node.js, Playwright and its Chromium installed. The scripts use the already prepared `.research/nextbrain-exvivo-20261027/package/` directory: the333 immutable plane/mesh payloads produced by the pinned source-preparation programs in `docs/nextbrain-source-review-20261027/`. Its manifest SHA-256 is `dfe1e6c2a50398175bc8e280dacec4f541c16f0c7327ce864c0b3f884dd7ad54`. No production app credentials or learner data are used; source requests are fulfilled from that local packet.

The archived `.cjs.txt` files are inert. Restore them to the expected research location:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, shutil, subprocess
root = Path.cwd()
docs = root / 'docs/nextbrain-context-recovery-20261027'
review = root / '.research/nextbrain-exvivo-20261027/context-epoch-review-20261027'
baseline = review / 'before-context-epoch'
baseline.mkdir(parents=True, exist_ok=True)
proof = json.loads((docs / 'before-proof.json').read_bytes())
commit = 'e2d2003d22f0e8516d9066ab15fc9ac5346c795d'
for name, digest in proof['sourceSHA256'].items():
    assert name in {'viewer.js', 'transport.js', 'index.html', 'viewer.css', 'manifest.json', 'config.json', 'labels.json'}
    raw = subprocess.check_output(['git', 'show', commit + ':web/anatomy/nextbrain/' + name])
    assert hashlib.sha256(raw).hexdigest() == digest
    (baseline / name).write_bytes(raw)
for source, target in [('reproduce-before.cjs.txt', 'context-epoch-before.cjs'),
                       ('reproduce-current.cjs.txt', 'context-epoch-current.cjs')]:
    shutil.copy2(docs / source, review / target)
PY
node .research/nextbrain-exvivo-20261027/context-epoch-review-20261027/context-epoch-before.cjs
node .research/nextbrain-exvivo-20261027/context-epoch-review-20261027/context-epoch-current.cjs
```

The before run is expected to exit1 and preserve the failure JSON; run the second command separately if the shell stops on error. The current run should exit0. If the historical Git object is absent, fetch that exact commit before the bootstrap step. Set `NODE_PATH` to the installed Playwright package directory when it is not in the repository's normal Node resolution path. The scripts write only their research receipts and start a temporary loopback server/headless browser, which are closed on exit.
