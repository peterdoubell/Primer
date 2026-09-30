# Knee ligament volumes and bundle-source review - 30 September 2026

**No newly verified segmented ACL/PCL bundle, POL-arm or attachment volume was
found in this bounded review.** The existing Z-Anatomy OPL is a genuine separate
source-named object and can be considered for **partial gross-course review**.
It is not measured tissue geometry. No runtime file, requirement, ledger entry
or approval status was changed by this investigation.

## Existing MRI-derived packages

The current [Malaya manifest](../web/anatomy/msk-mri-knee/manifest.json) has one
`Ligament_ACL` label/object (2,672 retained triangles) and one `Ligament_PCL`
label/object (2,732). Their source segmentation IDs and label values are
explicit, but there are no separate bundle labels or attachment footprints.
The [paired-source review](msk-malaya-knee-paired-source-review.md) likewise
does not resolve bundles or exact insertion boundaries. The
[original Malaya dataset](https://researchdata.um.edu.my/dataset.xhtml?persistentId=doi:10.22452/RD/5T6TZ7)
permits reuse under CC0; that does not verify anatomical completeness.

The current [Open Knee oks003 manifest](../web/anatomy/openknee-oks003/manifest.json)
contains ACL and PCL whole objects with 13,500 and 4,698 triangles respectively.
The [selected source connectivity map](../web/anatomy/openknee-oks003/SOURCE-ASSEMBLY.xml)
has ties/contact relations, not independently segmented attachment tissues or
bundle objects. The [primary model paper](https://link.springer.com/article/10.1007/s10439-022-03074-0),
Image Segmentation and Model Customization sections, distinguishes whole
segmented tissues, proximity/normal-derived model sets, spring stabilizers and
possible future bundle/layer refinements. Geometries retain CC BY-SA 3.0; MRI
archive terms remain separate. These major ligament envelopes cannot be
partitioned into named bundles by inference.

Leeds Knee 2 and Dryad are already reviewed in the workspace. Their acquired
inventories do not add the requested bundle or POL/OPL attachment volumes.
Leeds root constraints are spring elements, not root tissue geometry; see the
[Leeds review](msk-leeds-knee-source-progress.md) and
[Dryad review](msk-dryad-knee-source-progress.md). No repeat model downloads
were performed for these packages.

## Existing OPL: native object audit

The original `Joints100.fbx` was reacquired now from the pinned
[Z-Anatomy commit](https://github.com/LluisV/Z-Anatomy/tree/6c7f9016bd5899ac8edafd31b9900c151df42ed6).
Its 9,804,796 bytes and SHA-256 match the earlier original-source pin. This
review read the original FBX arrays directly, rather than relying on the
earlier inventory's polygon counts. Source staging remains under
`.research/knee-ligament-volume-sources/`; safe acquisition records are retained
in [the review folder](msk-knee-ligament-volume-source-review/acquisition.json).

| Field | Directly checked current evidence |
| --- | --- |
| Runtime asset | `za-joints-711785439` |
| Native model | `Oblique popliteal ligament.r`, model ID 711785439 |
| Native geometry | `Oblique popliteal ligament.001`, geometry ID 814296616 |
| Native object | 186 positions, 184 oriented quadrilateral faces; one `Ligament` material |
| Published buffer | 736 vertices retaining normal seams, 368 triangles, 186 unique positions |
| Connectivity | One connected component; Euler characteristic 2; zero boundary, nonmanifold or inconsistently wound edges |
| Nonplanarity | All three centered position singular values nonzero; not a planar material patch |
| Enclosed artist volume | Signed 0.465188365 cm3; not biological tissue volume or measured thickness |
| Native units/frame | Centimeters; +X patient left, +Y superior, +Z anterior; right object has negative X |
| Native X bounds | -9.738925934 to -5.381175518 cm |
| Native Y bounds | 41.106246948 to 48.212200165 cm |
| Native Z bounds | -6.545941830 to -3.503101110 cm |

Every transformed original position matches the published float32 position
set. All 184 oriented native quads are exhaustively represented by exactly two
published triangles each, preserving their orientation; no extra triangles or
degenerate triangles occur. This is a source-preservation result. It does not
prove absence of self-intersection or biological boundary accuracy.

Original FBX SHA-256:
`f4ba7a910cdaef99e31530f368628780d9f06b5d77853f8b721f47f67137e823`.
Published buffer SHA-256:
`af608d8a0a26c404bb4998bd8b0eb72586a2e0ef663564b777df7f5da6a4fe02`.

The [four native-frame views](msk-knee-ligament-volume-source-review/existing-opl-native-review.png)
were inspected after rendering. They show a thin, curved oblique artist band,
with a narrow upper end and a broader lower end, behind the source knee bones.
The faceting is visible. No separate arm, fiber bundle, histological layer,
attachment face or thickness measurement is supplied. The source name does not
establish that endpoints encompass the complete anatomical attachments.

The [pinned model notice](https://raw.githubusercontent.com/LluisV/Z-Anatomy/6c7f9016bd5899ac8edafd31b9900c151df42ed6/Resources/Models/License.txt)
requires Z-Anatomy and BodyParts3D lineage attribution and ShareAlike. The
existing OPL and this derivative projection retain CC BY-SA 4.0. The notice's
unrelated restricted third-party models were not acquired or imported.

**Implementable scope:** the already available, unchanged OPL could support an
unapproved `knee.oblique_popliteal_ligament.course` candidate with extent
`partial`, after the reader view is inspected and tied to current file hashes.
It cannot satisfy measured attachments, thickness, arm-specific anatomy,
segmented subject correspondence, or complete clinical-grade representation.
Do not substitute its artist volume for an MRI-derived tissue volume.

## Why bundle-named mechanical models do not close the gap

The official University of Denver
[OKS003 model-development specification](https://simtk.org/docman/view.php/1061/11497/DU_ModelDevSpec_OKS003_20180815.pdf)
was acquired (2,212,061 bytes; SHA-256
`37c79589c74d6d2bea0e012a1895ce6f15e9a22c182d39e8061896fb28346dc0`).
Pages 17-18 were rendered and inspected directly. It specifies ACL, PCL, POL,
PFL and other ligaments using one-dimensional tension-only nonlinear springs.
ACL AM/PL bundles each have two fibers, not separate segmented volumes.
Footprints are fitted rectangles/ellipses, with literature descriptions used
when MRI digitization is unreliable. Table 2's POL is one bundle/two fibers.
This is a planning specification; it alone does not prove the final delivered
model. It provides no basis for converting these connectors or fitted regions
into anatomical solid geometry. No Denver model bundle was downloaded.

The [2018 extended OpenSim knee study](https://link.springer.com/article/10.1186/s12938-018-0474-8),
Tibio-femoral geometry and connective tissues section, likewise represents 25
bundles through attachment sites and straight-line lengths. It does not supply
distinct measured bundle volumes. Neither set of fiber names authorizes
inventing tissue partitions.

## Other bounded primary-source leads

The [2021 KneeHub workflow comparison](https://pmc.ncbi.nlm.nih.gov/articles/PMC8086182/),
Ligament and Tendon Representations section, says CSU, DU and HSS use springs
or line segments. ABI uses non-specimen-specific ligament templates, while CC
segments whole ligaments. Thus neither a bundle name nor a continuum element
type proves measured bundle boundaries or attachment geometry. This review did
not acquire a new KneeHub model package.

The [2024 Wang et al. finite-element study](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1437684/full)
names OPL, arcuate popliteal, posterior capsules, PFL and meniscal attachments
and describes a tetrahedral knee model. The article's table also distinguishes
stiffness-based structures from continuum material coefficients. Without
native part/element definitions, their volume-versus-connector representation
cannot be confirmed. Its data-availability statement points to the article and
supplement/inquiries; this bounded inspection found no identified reusable
native OPL/POL mesh or separate data licence. Article open-access rights are
not evidence of a native asset's availability or boundaries. No author was
contacted and no model was reconstructed from figures.

## Reproduction and retained evidence

- [Native/current geometry audit](msk-knee-ligament-volume-source-review/existing-opl-geometry-audit.json).
- [Projection](msk-knee-ligament-volume-source-review/existing-opl-native-review.png).
- [Bounded source acquisition record](msk-knee-ligament-volume-source-review/acquisition.json).
- [Reproducible audit/render tool](../tools/anatomy_sources/audit_knee_ligament_volume_sources.py).

Run the audit with Python 3.12, NumPy and Matplotlib, using the retained pinned
FBX in `.research/knee-ligament-volume-sources/`. It checks source and runtime
hashes before computing geometry evidence. In the current workspace:

```sh
PYTHONPATH="$PWD/.research/lumase-plot-deps" /Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/anatomy_sources/audit_knee_ligament_volume_sources.py
```

The review changes only research evidence. All clinical approval gates remain
pending; ACL/PCL bundles, POL arms, attachment footprints and complete MSK
coverage still require stronger anatomical evidence.
