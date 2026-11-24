# The biliary reader's "common hepatic duct" object, shown as two ducts (2026-11-24)

## The decision

The project owner asked for the biliary atlas's common hepatic duct label to be corrected.

The biliary 3D reader (`web/anatomy/bp3d-biliary-4.3`) showed BodyParts3D 4.3 object FJ3079 under the source's label,
"Common hepatic duct". The object also holds the common bile duct, and the source has no common bile duct object.
The reader now shows the object in two parts:

| Label in the reader | Part |
| --- | --- |
| Common hepatic duct · FJ3079 above the cystic duct | from the hepatic duct confluence down to the cystic duct junction |
| Common bile duct · FJ3079 below the cystic duct | from the cystic duct junction to the lower end of the object |

## Why the label was wrong

- The right and left hepatic duct objects meet FJ3079 at its top.
- The source's two cystic duct objects (FJ3080 and FJ4526) touch FJ3079 between 20 and 24 mm below that confluence,
  measured along the duct's course at the junction.
- The object runs on for about 60 mm below the cystic duct. Its whole height is 84 mm.
- The common bile duct is the duct below the union of the cystic duct and the common hepatic duct. So about three
  quarters of the object is common bile duct.
- Clarkson and Whipple's comparison of anatomical resources (PubMed 30815072) had flagged this segmentation.

## How the object was divided

`tools/anatomy_sources/partition_biliary_duct.py` does it, and `review.json` holds the numbers.

1. A duct vertex within 1 mm of a cystic duct vertex belongs to the junction. There are nine, over 4.2 mm of the duct.
2. One plane passes through their mean, perpendicular to the duct's course there.
3. Each source triangle goes whole to the part on whose side of the plane its centroid lies.

No geometry is made. No vertex is moved, and none is added. The two parts together hold exactly the 1,364 source
triangles, each once, with the source's float32 coordinates. A test repeats this from the delivered files and the kept
copy of the source object (`evidence/FJ3079.mesh.gz`, the file the reader delivered until now).

The division is placed to within about 3 mm: the cystic duct touches the object over 4.2 mm, and the boundary between
the parts follows whole triangles over 6.0 mm.

## Limits

- **No radiologist has reviewed the division.** It rests on measurement of the source meshes.
- The source's cystic duct insertion is one modelled anatomy. Variants are not shown.
- An earlier review of these objects records that vertex proximity does not prove a biological junction.
- The lower part ends where the source object ends. The intrapancreatic and intramural segments are not marked.
- The surface shows neither lumen nor wall alone.

## Bindings

Neither part is bound to a requirement. The binding rule needs a mesh's own source label to name the requirement, and
these names come from this division. The body-reader binding review of 2026-11-19 lists both parts under `not_recorded`
and carries an amendment.

## Licence

BodyParts3D 4.3 is CC BY-SA 2.1 Japan. The division is an adaptation, shared under the same licence. The reader's
attribution line names it.

## Files

- `web/anatomy/bp3d-biliary-4.3/`: two part meshes in place of `FJ3079.mesh.gz`; `surfaces.json`, `index.html`,
  `provenance.json` and `delivery.json` follow.
- `tools/anatomy_sources/partition_biliary_duct.py`: the division and the reader files.
- `docs/body-reader-model-bindings-20261119/`: the amendment.
- `docs/bp3d-biliary-4.3/README.md`: the earlier statement that no part is assigned a duct identity now gives its dates.
- `tests/test_biliary_duct_partition.py`.
