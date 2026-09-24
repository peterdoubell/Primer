# Biology illustration review

## Introductory stages 0–1

All eleven current 800px plates were inspected against their curriculum alt text
and captions. This is a content/layout review, not a claim that all high-resolution
views, browser sizes or model states were reverified in this pass.

Five native-source plates were corrected and their responsive pairs regenerated:

- Living/not living: roots now stop above the process labels.
- Plant growth: soil and root layouts leave the stage explanations unobscured.
- Habitats: cactus and polar captions fit their panels without reducing type size.
- Food chains: grass now has narrow blades; species labels no longer collide.
- Staying healthy: organ icons no longer cover text; the sleep caption is shorter.

The remaining six plates were preserved. The frog cycle is a detailed authored
organism illustration, whereas the sense and organ-system pictures are explicitly
schematic. The season picture bounds its example to a temperate year, and the
health footer does not promise outcomes or replace medical care. The five-sense
picture introduces familiar channels rather than cataloguing every human sense.
Plant-growth stages depict a flowering-plant example, not every plant lineage.

Seven focused biology tests pass. Added regressions measure root/caption clearance
and the actual font bounds of food-chain labels; caption-bound checks now include
habitats and health. Individual observations and asset fingerprints are recorded
in `illustration-reviews.json`. This does not complete the all-subject release audit.

## Stage 2

Seven current 800px plates were inspected. The classification diagram's other-
archaea branch and specimen were moved right and upward to separate its label
from the frame and the eukaryote label. The asexual-route offspring label was
shortened to avoid colliding with the shared growth panel. Both corrected images
were rerendered and visually checked. Photosynthesis alt text now explicitly
distinguishes the balanced equation's coefficients from its schematic icons;
no atom or molecule count should be inferred from the number of pictorial marks.

Preserved examples include three contrasting cell specimens, separate body-waste
routes, the energy/matter distinction in an ecosystem, and a base-ten organism-
size axis whose yeast/animal-cell overlap is explicit. The reproduction diagram
illustrates a mitotic eukaryotic asexual route, not all forms of asexual reproduction.

## Stage 3

Seven current 800px plates were inspected. Genetics prose is wrapped inside the
phenotype panel and avoids implying a simple additive equation. Cell biology no
longer draws a mitochondrion behind the ribosome/transcript route, and the
translation label has an opaque callout. Ecology flux labels and the opposing
photosynthesis arrow are separated. Microbiology clone/memory labels no longer
overlap, and its timeline uses qualitative phases instead of unequally spaced
numeric days. Botany's soil label is clear of roots.

Evolution alt text now describes the actual two populations: 4/12 and 9/12
spotted beetles. Its caption distinguishes phenotype counts from measured diploid
allele frequencies. The separate authored anatomical specimens remain intact;
the caption already distinguishes them from a connected circulation-route model.
Fifteen biology/review tests pass, including actual beetle counts and repaired
label bounds. This remains a bounded review, not deployment verification.

## Stages 4–5

All twelve current 800px plates were inspected, completing the 37-lesson biology
content/layout pass at this resolution. Eight native plates were corrected:

- Biochemistry: unreadable subscript-a glyphs replaced with higher/lower barrier
  labels; the lower-barrier label was moved clear of the curve.
- Neuroscience: the authored voltage plot is identified as schematic, not measured.
- Evolutionary biology: the lineage-inference label was moved clear of its arrow.
- Physiology: the response caption, sweat heading, detector and blood-flow text
  no longer collide with the feedback diagram.
- Ethology: cooperation variables fit inside their panel on two lines.
- Systems biology: the missing subscript-s glyph is replaced with `P_s`.
- Immunology: APC, contact/signal and memory-cell labels are separated from
  neighbouring cells and labels; effector and memory remain parallel branches.
- Frontiers: legend marks, threshold label and captions have dedicated space.

Ethology, computational-biology and frontiers alt text now describes the actual
panels rather than an obsolete table/matrix layout. The frontier caption explicitly
identifies illustrative curves/spectral marks, not experimental or detection
claims. Evolutionary-biology caption likewise bounds its trait counts and drift
replicates. The remaining authored molecular/developmental pictures and the
genomics/computational diagrams were preserved.

Sixteen focused biology/review tests pass. The new font check intercepts actual
drawn labels across all 85 generated natural-science plates and rejects glyphs
that resolve to the font's missing-character box. The 93-lesson natural-science
checker verifies all 186 responsive rasters, including deterministic regeneration
of its 85 generated plates. Neither check substitutes for final browser/model
verification or the remaining subjects' visual review.
