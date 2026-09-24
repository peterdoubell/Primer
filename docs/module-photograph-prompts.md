# Module photograph prompts and provenance

Created: 2026-09-23.

These 22 photorealistic contextual images were generated specifically for Primer using the built-in OpenAI `image_gen.imagegen` tool (not the API/CLI fallback). The built-in service does not expose a model identifier, so none is asserted. Each asset used its own prompt. The two images in each subject are shared across related modules; they are not individually commissioned depictions of every lesson. The curriculum's authored diagrams remain the source for precise explanations.

All final images are labeled AI-generated in the manifest. The images show illustrative scenes, not documentary evidence, authenticated historical artifacts, known individuals, clinical patient data, or diagnostic scans. The historical archive variant was regenerated once to remove incidental book-spine lettering; only the accepted variant is included below.

Final assets are under `web/illustrations/photoreal/`, served at `/app/illustrations/photoreal/`. Each accepted output is converted with Pillow 11.3.0 to WebP quality 85, method 6, using Lanczos resizing to 800×450 and 1600×900. The tiny native aspect-ratio rounding difference is normalized to exact 16:9 so both responsive variants have identical proportions. No content was painted, composited or otherwise edited. Original generated PNGs remain in the tool's original directory. WebP files, dimensions and byte limits were checked after export. Manifest: `data/module-photographs.json`.

## math — context

- Final files: `web/illustrations/photoreal/math-context-800.webp` and `web/illustrations/photoreal/math-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-bb446c02-7716-4133-af76-6e74141cb3bf.png`.
- Alt: Wooden geometric solids, counting stones and a drawing compass on a sunlit learning table.
- Caption: Geometric solids and counting materials connect mathematical ideas with physical objects. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for mathematics lessons in Primer, an educational website.
Scene: a quiet light-filled learning studio, tabletop at close eye level.
Subject: carefully arranged real wooden geometric solids including a cube, sphere, cylinder and triangular prism, a small group of smooth counting stones, a brass drawing compass lying safely closed and a folded sheet of unmarked graph paper.
Style: premium documentary still-life photography, unmistakably realistic physical objects with natural wood grain, tiny surface imperfections and believable soft shadows; medium-format detail, balanced uncluttered composition.
Composition: landscape 16:9, photograph fills entire frame, objects grouped naturally in center with calm surrounding space. Warm daylight from a nearby window, restrained neutral colors.
Constraints: no visible writing, numbers, labels, brands, watermarks, borders, collage, diagrams, CGI look or surreal geometry. This is a contextual image of mathematics learning materials, not an equation or diagram.
```

## language — context

- Final files: `web/illustrations/photoreal/language-context-800.webp` and `web/illustrations/photoreal/language-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-f33cbf90-848c-42b6-a240-4e08e8621a2b.png`.
- Alt: An open blank book, clothbound books and a fountain pen on a library desk.
- Caption: Books and writing materials provide a physical setting for language and communication. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a quiet library reading desk beside a large softly lit window, an open clothbound book with blank cream pages viewed at an oblique angle so no print is shown, three closed clothbound books with no spine titles, a fountain pen and a stack of handwritten-free correspondence paper. Fine paper fibers, woven book cloth and beautifully weathered oak are the visual subjects. Rich warm daylight, peaceful scholarly atmosphere, shallow depth of field with softly blurred bookshelves in the background. Simple natural still-life composition, ample breathing room.
```

## physics — context

- Final files: `web/illustrations/photoreal/physics-context-800.webp` and `web/illustrations/photoreal/physics-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-ff0b957a-88ee-41a5-8ea4-57db0bfc60cd.png`.
- Alt: Glass lenses and a prism on an optics bench beside a softly projected rainbow.
- Caption: An optics workbench brings light, measurement and physical experimentation into view. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a real physics optics workbench, with a small triangular clear glass prism, a precision lens mounted upright in a dark metal holder, a second lens and an optical rail in a teaching laboratory. A narrow shaft of white sunlight crosses the prism and a subtle continuous rainbow spectrum lands on a matte white screen on the table. Show only a plausible small optical effect in physical glass, not floating graphics or laser fantasy. Polished glass, brushed metal, dustless bench, window illumination and detailed optical reflections. Oblique close view, modest depth of field, engaging scientific still life.
```

## biology — context

- Final files: `web/illustrations/photoreal/biology-context-800.webp` and `web/illustrations/photoreal/biology-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-417aa85e-ae22-46c4-81b8-187f5aa288e1.png`.
- Alt: A young green plant with veined leaves and dew beside a hand lens in a greenhouse.
- Caption: A living plant invites close observation of growth, structure and the natural world. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: an intimate botanical field-study photograph of a living young broadleaf plant growing in dark moist soil in a small terracotta pot, viewed at leaf height beside a sunlit greenhouse window. Several crisp green leaves with clearly visible branching veins, a tender new leaf, droplets of dew, a gently blurred garden background and one elegant glass hand lens lying on the potting bench. Make the living leaf textures and growth the hero. Real macro botanical photography with soft natural green and warm earth tones, plausible veins and leaf attachments, calm wide composition.
```

## chemistry — context

- Final files: `web/illustrations/photoreal/chemistry-context-800.webp` and `web/illustrations/photoreal/chemistry-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-a15b0178-b760-4d54-bc14-13b361bea38f.png`.
- Alt: Laboratory flasks, small glass vials and stirring rods on a daylight-lit bench.
- Caption: Laboratory glassware provides context for observing and investigating matter. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a pristine but lived-in chemistry teaching laboratory bench with a clear conical flask containing a small amount of translucent pale blue solution, an empty round-bottom flask secured upright in a proper metal clamp, three small unlabeled glass sample vials in a wooden rack, and a glass stirring rod resting flat on a clean tray. Wide eye-level still life, beautiful believable glass refraction and reflections, soft daylight from a side window, softly blurred laboratory shelving behind. All containers must be ordinary plausible glassware, no smoke, flames, spills, theatrical vapor or extravagant colors. Calm analytical atmosphere.
```

## cs — context

- Final files: `web/illustrations/photoreal/cs-context-800.webp` and `web/illustrations/photoreal/cs-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-f142fc3b-7f9a-4c4b-a930-01c3036f89fe.png`.
- Alt: A processor, capacitors and fine conductive traces on a green computer motherboard.
- Caption: A computer motherboard shows the physical hardware beneath digital systems. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: macro photograph of a genuine-looking computer motherboard on an electronics workbench, a single square central processing chip without lettering surrounded by tiny capacitors, copper traces, sockets and a folded antistatic mat. Precisely manufactured green circuit substrate, solder joints and brushed aluminum cooling fins, convincing real scale and subtle wear. Low oblique angle, sharp central chip with measured shallow depth of field and a soft dark technical background. Soft window light and understated practical workbench illumination, not neon or futuristic. No binary numbers, floating code, UI screens or science fiction imagery.
```

## history — context

- Final files: `web/illustrations/photoreal/history-context-800.webp` and `web/illustrations/photoreal/history-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-536ece2b-fb95-461f-9ad5-606bc96d9a77.png`.
- Alt: Weathered pottery, clay fragments and a bronze buckle on a conservation table.
- Caption: Illustrative archaeological objects show the kinds of material evidence historians investigate. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: documentary still-life photograph of historical material culture on a museum conservation workbench: an unmarked weathered terracotta earthenware bowl, several irregular pottery sherds with visible fired-clay texture, one simple bronze buckle with natural patina, a soft conservation brush and folded neutral archival tissue. These are generic illustrative objects, not replicas of a named culture or specific artifact. Close wide view of physical evidence with respectful restrained museum lighting, detailed handmade clay surfaces and warm neutral tones. No reconstruction of an ancient scene, people, inscriptions, invented symbols, fake museum labels or dramatic treasure imagery.
```

## earth — context

- Final files: `web/illustrations/photoreal/earth-context-800.webp` and `web/illustrations/photoreal/earth-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-a3575101-05c2-4f9a-92b5-7de04b923f55.png`.
- Alt: A clear river passing layered rock and forested mountains under soft cloud.
- Caption: Water, exposed rock layers and vegetation show interacting parts of the Earth system. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a sweeping yet intimate natural landscape showing a freshwater river winding through visibly layered sedimentary rock in a green mountain valley after rain. Foreground rounded pebbles and a shallow transparent stream reveal real stone textures, middle distance exposes horizontal rock strata, distant forested slopes fade naturally into soft mist. Credible terrestrial geology and atmosphere, overcast daylight with a soft break of sun, rich but restrained greens and stone colors. Wide documentary landscape photograph with excellent depth and fine natural detail. No buildings, roads, maps, labels, surreal mountains or exaggerated fantasy terrain.
```

## arts — context

- Final files: `web/illustrations/photoreal/arts-context-800.webp` and `web/illustrations/photoreal/arts-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-b7f3f61b-81ed-4bd6-a2d2-b53c8575956c.png`.
- Alt: Used paintbrushes, a wooden color palette, clay vessel and blank sketchbook in an art studio.
- Caption: Studio materials connect creative ideas with texture, color and the act of making. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a real artist's studio worktable in beautiful soft north-window daylight. A ceramic jar holds several visibly used paintbrushes, a wooden palette bears small tactile dabs of restrained oil colors, a brass palette knife lies flat, and a small unpainted clay vessel rests beside folded linen and a sketchbook showing blank paper. Paint-stained oak, glossy paint, brush bristles and clay surface provide rich authentic detail. Composition intimate, balanced and naturally untidy, with softly blurred canvas stretcher frames behind. No finished artwork, invented images within images or text.
```

## mind — context

- Final files: `web/illustrations/photoreal/mind-context-800.webp` and `web/illustrations/photoreal/mind-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-61cb7944-cf3c-48ef-b9b4-b0e42b2522cd.png`.
- Alt: Three fictional adults listening and talking together around a table in a bright room.
- Caption: An illustrative conversation provides context for attention, communication and social thinking. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: candid editorial photograph of three fictional adults with varied skin tones seated at a round oak table in a comfortable sunlit community learning room, attentively discussing an idea together. One person gestures naturally with an open relaxed hand while the other two listen, with believable expressions, ordinary casual clothing, natural anatomy, a few blank index cards on the table and a glass of water. The people are invented, no recognizable real person. Wide medium shot, warm daylight, gentle background blur, subtle relaxed human connection rather than stock-photo posing. No writing, visible screens or brain graphics.
```

## radiology — context

- Final files: `web/illustrations/photoreal/radiology-context-800.webp` and `web/illustrations/photoreal/radiology-context-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-6be3438a-f6f5-4c8f-8d64-3cb204d9d897.png`.
- Alt: An unbranded MRI scanner and empty patient couch in a modern examination room.
- Caption: Imaging equipment provides clinical context; this generated scene contains no patient or diagnostic scan. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, labels, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a realistic modern hospital magnetic resonance imaging examination room, clean white cylindrical MRI scanner with a wide round bore, aligned patient couch extending naturally forward, soft ceiling lighting, simple pale walls and a clear viewing window to a control room. Photograph from a three-quarter angle with wide architectural lens, accurate substantial real equipment scale and quiet clean clinical atmosphere. The scanner has no brand or logo. No people, patients, anatomy, patient scans, imaging screens, needles, text or warning labels. This is a contextual equipment photograph, not diagnostic medical imagery.
```

## math — practice

- Final files: `web/illustrations/photoreal/math-practice-800.webp` and `web/illustrations/photoreal/math-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-827ac647-80dc-459b-baf7-03d9a32a4e2d.png`.
- Alt: A caliper around a wooden cylinder, a clear set square, coiled cord and brass balance on a workbench.
- Caption: Measuring tools connect mathematical quantities with length, shape and comparison. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No words, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: macro still-life photograph of mathematical measurement tools on a real drafting workbench. A brushed steel vernier caliper slightly open around a small smooth wooden cylinder, a transparent triangular set square without printed numbering, a compact brass balance with two empty pans, and a neatly coiled plain measuring cord. Oblique wide close-up, shallow depth of field with the caliper and cylinder crisp, soft cool daylight, richly detailed wood and metal. Ordinary precise tools with plausible mechanical construction, no floating geometry, equations or decorative graphics.
```

## language — practice

- Final files: `web/illustrations/photoreal/language-practice-800.webp` and `web/illustrations/photoreal/language-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-324b5bc1-94b6-47a9-8f95-314509f8d6e9.png`.
- Alt: An ink roller, metal printing sorts and cream paper beside a traditional printing press.
- Caption: Printing materials show a physical process for reproducing and sharing language. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No words, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: documentary photograph of a traditional letterpress printing workshop. Close-up of a real ink roller resting beside a shallow wooden printer's type tray, stacks of thick cream paper and a small manual printing press softly blurred in the background. The metal printing sorts sit face-down or sideways so their textured metal sides, not letters, are visible. Tactile ink, worn oak and dark cast iron, soft workshop window light, balanced wide composition. No visible printed text, readable letters, posters, logos or historical costume.
```

## physics — practice

- Final files: `web/illustrations/photoreal/physics-practice-800.webp` and `web/illustrations/photoreal/physics-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-320f7ba2-561d-483a-892c-e3f8bd0ae516.png`.
- Alt: A brass pulley with two hanging masses, a coil spring and spare weights on a laboratory table.
- Caption: Mechanical apparatus provides context for investigating motion, force and energy. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No words, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: close documentary photograph of a well-made teaching mechanics apparatus on a wooden laboratory table: a small solid brass pulley wheel secured in a sturdy upright metal stand, one continuous braided cord seated naturally in the groove with one small metal mass hanging from each end, both hanging freely at rest. A coil spring and plain metal weights lie beside it on the table. Show credible ordinary workshop construction with correct physical attachments and plausible balance. Soft side daylight, intricate metal grain and cord fibers, quiet engineering atmosphere. No force arrows, labels, floating objects or impossible mechanisms.
```

## biology — practice

- Final files: `web/illustrations/photoreal/biology-practice-800.webp` and `web/illustrations/photoreal/biology-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-2085582c-7091-4b5d-8e60-372e60b65edb.png`.
- Alt: A binocular microscope, glass slides and a leaf specimen on a bright laboratory bench.
- Caption: Observation tools extend the scale at which living things can be studied. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a realistic optical microscope on a modern biology teaching bench, correctly proportioned binocular eyepieces, objective turret and glass slide on the stage. Beside it a small covered clear dish holding a green leaf and a tidy tray with plain glass slides. The microscope is unbranded, no specimen imagery appears on any screen. Soft bright daylight, honest brushed metal, glass and ceramic textures, plant-filled laboratory window softly blurred behind. Quiet close wide composition focused on tools for careful observation, no people, fantastical cells or microorganisms.
```

## chemistry — practice

- Final files: `web/illustrations/photoreal/chemistry-practice-800.webp` and `web/illustrations/photoreal/chemistry-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-915eaea3-2003-4aeb-9875-853d437eb87e.png`.
- Alt: Clear, purple and white crystalline mineral specimens on a tray beside a hand lens.
- Caption: Crystal specimens invite observation of the visible structures and properties of materials. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: macro studio photograph of three physical mineral specimens on a pale gray laboratory sample tray: a small transparent quartz crystal cluster, a modest chunk of deep purple amethyst, and a white cubic salt crystal specimen. Show realistic natural crystal facets, tiny chips and imperfect surfaces, credible modest hand-sized scale. A simple unmarked glass hand lens rests beside the tray. Soft side daylight brings out refraction and mineral color without exaggerated glowing effects. Balanced wide still life of actual material textures, no labels, floating atomic diagrams or impossible giant crystals.
```

## cs — practice

- Final files: `web/illustrations/photoreal/cs-practice-800.webp` and `web/illustrations/photoreal/cs-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-9b3efa07-4157-492f-97e3-6a4136088477.png`.
- Alt: Rows of server cabinets with neatly organized blue and gray network cables.
- Caption: Servers and network cables reveal the physical infrastructure connecting digital systems. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: documentary photograph looking down a tidy real data-center aisle, rows of modest black server cabinets with metal mesh doors, neatly routed blue and gray Ethernet patch cables visible through one open rack, and sparse tiny green status lights. Accurate physical server infrastructure, soft cool overhead practical lighting, clear perspective, restrained contrast and detailed connectors in foreground. A quiet unoccupied working environment, not futuristic cyberpunk, no dramatic neon, floating data, screens, code, logos or readable rack labels.
```

## history — practice

- Final files: `web/illustrations/photoreal/history-practice-800.webp` and `web/illustrations/photoreal/history-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-6e8cbbed-7573-4811-bab9-3e1f7dea4120.png`.
- Alt: Unmarked archive folders, preservation boxes and tied document rolls beside a magnifying glass.
- Caption: Archival materials provide context for preserving and investigating evidence from the past. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a quiet historical archive storage desk with an open plain gray acid-free archive box holding several completely unmarked cream document folders, a second closed archival box with no label, three rolled blank-facing vellum sheets tied with plain cotton tape, a brass magnifying glass and a pair of thin cotton conservation gloves. Focus on surviving materials and preservation, not historical reconstructions. Rich real paper edge texture, old oak wood grain and soft window daylight. Background softly blurred featureless shelving with anonymous boxes. There must be absolutely no books, book spines, printed text, handwriting, symbols, readable documents, captions or labels anywhere in the image.
```

## earth — practice

- Final files: `web/illustrations/photoreal/earth-practice-800.webp` and `web/illustrations/photoreal/earth-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-ba713da5-2060-4325-8f60-444d6d5b933a.png`.
- Alt: A refracting telescope on rocky ground beneath a twilight sky with stars.
- Caption: A telescope and open sky connect Earth observation with astronomical inquiry. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a real small amateur refracting telescope on a stable tripod at a remote rocky observation site at late blue twilight, its tube pointed gently upward, with a restrained starry sky above distant low mountains. The telescope is unbranded, eyepiece and finderscope plausible, rock and sparse grass visible in soft residual dusk light. Wide cinematic but truthful outdoor photography, faint natural Milky Way texture and a modest number of pinpoint stars without oversized planets or fabricated constellations. No people, trails, orbit lines, lettering or fantasy astronomical scenery.
```

## arts — practice

- Final files: `web/illustrations/photoreal/arts-practice-800.webp` and `web/illustrations/photoreal/arts-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-e74c0792-d0dd-4e4d-a40c-bd4cd151c834.png`.
- Alt: A wooden violin and bow in a velvet-lined case beside an upright piano.
- Caption: Musical instruments connect sound, performance and the craft of making art. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: intimate real chamber-music rehearsal room with a polished wooden violin resting safely in an open velvet-lined case, its bow lying in the case beside it, and the softly blurred keys and warm wood side of a small upright piano behind. The violin has four strings, plausible bridge and tailpiece, gentle handmade varnish wear and realistic fine grain. Natural afternoon window light, warm restrained colors, calm uncluttered wide still life celebrating musical materials and craft. No sheet music, text, musician, logos, flying musical notes or surreal instruments.
```

## mind — practice

- Final files: `web/illustrations/photoreal/mind-practice-800.webp` and `web/illustrations/photoreal/mind-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-f2be6e7c-ed42-4667-9f46-ba35bfb9cd2b.png`.
- Alt: Cards with simple colored shapes, wooden tokens and an hourglass on a table.
- Caption: Simple sorting materials provide context for exploring attention, memory and decisions. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a real psychology learning activity laid out on a quiet wood table: several thick plain cards face up showing only simple colored circles, triangles or squares, one short stack of identical face-down neutral cards, a plain wooden hourglass with sand, and a few smooth wooden sorting tokens. Calm ordinary experimental materials for observing memory, attention and choice. No people, no labels or instructions, no printed numbers, no brain models, no claim that it is a named diagnostic test. Soft window daylight, crisp tactile paper and wood, wide close view with an uncluttered composition.
```

## radiology — practice

- Final files: `web/illustrations/photoreal/radiology-practice-800.webp` and `web/illustrations/photoreal/radiology-practice-1600.webp`.
- Tool output: `/Users/peter/.codex/generated_images/01a0cfc8-4658-7461-8549-1175e30549ec/exec-3ece11ef-d1ff-4062-8c84-a3b71d393160.png`.
- Alt: An ultrasound cart with dark screens and two probes beside an empty examination couch.
- Caption: Ultrasound equipment provides clinical context; no patient or diagnostic image is shown. AI-generated contextual image, shared across related modules.

Exact accepted generation prompt:

```text
Use case: photorealistic-natural
Asset type: wide contextual photograph for Primer educational lessons, landscape 16:9.
Style: premium documentary photography, credible real physical objects, natural material texture and tiny imperfections, balanced restrained colors, photograph fills entire frame. No text, writing, logos, brands, watermarks, collage, borders, diagrams or CGI appearance.
Subject and scene: a realistic modern unbranded ultrasound equipment cart in an empty clinical examination room, with an entirely dark switched-off display, plausible control console with unlabeled controls, two ultrasound transducers secured in their holders and neatly looped probe cables. A clean examination couch sits softly out of focus behind it. Close three-quarter wide view, soft neutral clinical daylight, credible molded plastic and rubber cable textures. No patients, people, scans, anatomy, labels, measurement numbers, logos or visible words. Equipment context only, absolutely no diagnostic image on the screen.
```
