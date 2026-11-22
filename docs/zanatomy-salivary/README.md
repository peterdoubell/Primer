# Salivary gland bodies and duct courses

The neck ultrasound, MRI neck spaces and cervical lymph-node references expose the same gross atlas. The adult model shows six gland bodies, four modelled ducts and eight orientation landmarks. Each control corresponds to one named object in the Blender scene. These objects share geometry across sides. Gland subdivisions, microscopic boundaries, duct patency, lesions, individual lymph nodes and ultrasound appearances require their own evidence.

The publisher distributes the atlas under CC BY-SA 4.0, with BodyParts3D attribution. The selected assets contain none of the inner-ear or kidney models for which the publisher identifies different terms. The publisher's licence and full credits are also available in the reader. [Pinned atlas archive](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/ded1a55381328f3f242426f0e8e711c5fca62c14/Z-Anatomy.zip) · [Publisher licence](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/ded1a55381328f3f242426f0e8e711c5fca62c14/License.txt)

The packager evaluates the original, author-supplied Blender modifiers and curve geometry, transforms vertices into the atlas world frame and converts metres to millimetres. It uses Blender's loop triangles without additional smoothing or decimation. For reflected world transforms, it reverses triangle winding. The shipped surfaces have 18,356 vertices and 36,650 triangles. The section view draws their intersections with a plane at the displayed atlas coordinate. A cross-section through a modelled duct describes the tube as drawn by its author.

Use Blender 4.2.23 in background mode with automatic script execution disabled. From the repository root, run the two commands with the original scene path in place of `Startup.blend`.

```sh
blender --background --factory-startup --disable-autoexec Startup.blend --python-exit-code 1 --python tools/anatomy_sources/export_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary
blender --background --factory-startup --disable-autoexec Startup.blend --python-exit-code 1 --python tools/anatomy_sources/verify_zanatomy_salivary.py -- web/anatomy/zanatomy-salivary
```

The independent comparison checks every vertex through Blender's native matrix-vector transform and every source triangle against the decoded files. The largest coordinate difference was 0.0001193 mm after float32 rounding. This comparison establishes fidelity to the published artistic model. Clinical anatomical validation remains open.
