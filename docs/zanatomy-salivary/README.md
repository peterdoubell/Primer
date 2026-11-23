# Salivary gland bodies and duct courses

The neck ultrasound, MRI neck spaces and cervical lymph-node references expose the same gross atlas. The adult model shows six gland bodies, four modelled ducts and eight orientation landmarks. Each control corresponds to one named object in the Blender scene. These objects share geometry across sides. Gland subdivisions, microscopic boundaries, duct patency, lesions, individual lymph nodes and ultrasound appearances require their own evidence.

The publisher distributes the atlas under CC BY-SA 4.0, with BodyParts3D attribution. The selected assets contain none of the inner-ear or kidney models for which the publisher identifies different terms. The publisher's licence and full credits are also available in the reader. [Pinned atlas archive](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/ded1a55381328f3f242426f0e8e711c5fca62c14/Z-Anatomy.zip) · [Publisher licence](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/ded1a55381328f3f242426f0e8e711c5fca62c14/License.txt)

The packager evaluates the original, author-supplied Blender modifiers and curve geometry, transforms vertices into the atlas world frame and converts metres to millimetres. It uses Blender's loop triangles without additional smoothing or decimation. For reflected world transforms, it reverses triangle winding. The shipped surfaces have 18,356 vertices and 36,650 triangles. The section view draws their intersections with a plane at the displayed atlas coordinate. A cross-section through a modelled duct describes the tube as drawn by its author.

Use Blender 4.2.23 in background mode with automatic script execution disabled. From the repository root, run the two commands with the original scene path in place of `Startup.blend`.

Both tools accept only `web/anatomy/zanatomy-salivary` in the checkout containing the executed script. The absolute path to that same directory is also accepted. Other output directories, unlisted package filenames and symbolic links in the package directory or its members are rejected before package I/O.

```sh
blender --background --factory-startup --disable-autoexec Startup.blend --python-exit-code 1 --python tools/anatomy_sources/export_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary
blender --background --factory-startup --disable-autoexec Startup.blend --python-exit-code 1 --python tools/anatomy_sources/verify_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary
```

For scratch reproduction, make an isolated checkout, change to its root and run its copies of both tools with the same relative package path. For example:

```sh
git worktree add --detach /tmp/salivary-reproduction HEAD
cd /tmp/salivary-reproduction
```

Run the two Blender commands above there, using the absolute path to the pinned original `Startup.blend`. The export writes only that checkout's package. Compare its package against the reviewed revision with `git diff --exit-code -- web/anatomy/zanatomy-salivary`; a faithful reproduction leaves every file unchanged. The verifier then checks those scratch files against the original scene independently.

The independent comparison checks every vertex through Blender's native matrix-vector transform and every source triangle against the decoded files. The largest coordinate difference was 0.0001193 mm after float32 rounding. This comparison establishes fidelity to the published artistic model. Clinical anatomical validation remains open.
