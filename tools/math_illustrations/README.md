# Mathematics illustration sources

The exact lesson diagrams are rendered by the cohort modules in this folder.
They deliberately use deterministic coordinates, counts, plots, and labels so
the image can be checked against the mathematics.

The release rubric applies to every mathematics lesson from Seedling through
Forest: a plate must explain a relationship, operation, invariant, comparison,
boundary case, mechanism, or misconception. Decorative or merely atmospheric
imagery does not satisfy the contract, even when its caption is informative.
The inventory check therefore requires one local responsive plate for every
mathematics node, and visual QA reviews both the 1600px and 800px render.

An early editorial candidate for `math.5.frontier` was created with OpenAI's
built-in image generator and visually inspected. It was intentionally replaced
by a deterministic proof-versus-evidence plate when the release rubric was
tightened to require explanatory insight in every image. The exploratory prompt
was:

> Create one landscape educational illustration for a mathematics learning
> website, aspect ratio 8:5, with generous safe margins. A warm tactile
> watercolor-and-colored-pencil scene on cream paper: an open research notebook
> becomes a quiet landscape of branching unfinished mathematical paths. Include
> subtle, visually coherent motifs suggesting a graph, a knot, a number spiral,
> a curved surface, and a wave field, all connected by faint hand-drawn lines
> toward a softly lit horizon. The mood is curious, rigorous, welcoming, and
> unfinished—the frontier is made of open questions. Primer editorial
> illustration style, muted teal, ink blue, plum, ochre, and coral, soft paper
> grain, strong central composition, readable at small size. No people, no
> equations, no numbers, no words, no labels, no border, no logo, no watermark.
> Keep all important content away from the outer 8 percent for later cropping.

Install the tool-only raster dependency into the project environment, then
render and integrate the full set from the repository root:

```bash
.venv/bin/pip install -r tools/requirements-math-illustrations.txt
.venv/bin/python tools/generate_math_illustrations.py --render --overwrite
.venv/bin/python tools/generate_math_illustrations.py \
  --sync-curriculum --check --contact-sheet /tmp/primer-math-contact-sheet.png
```

Rendering validates all output collisions before writing the deterministic
cohort. The image-generator Frontier candidate is provenance only and is not
shipped or required to reproduce the site.
