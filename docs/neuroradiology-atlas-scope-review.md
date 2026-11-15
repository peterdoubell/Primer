# Neuroradiology atlas mapping correction

Inspection of the actual registered brain manifest found only gross right/left cerebral hemisphere, cerebellar and ventricular meshes. The deep-grey reporting step incorrectly selected the four ventricular meshes. Other steps similarly selected ventricles for veins or hemispheres for spinal/optic anatomy.

Fourteen steps across brain anatomy, MS, venous sinus thrombosis and intracranial hypotension now distinguish available orientation context from missing target anatomy. Incorrect part selections were removed. Partial cerebral/cerebellar context remains where relevant, with specific limits. The reporting fields, clinical finding phrases, measurements and examination instructions were preserved; no requested structure was removed from the clinical scope.

The optional anatomy note is validated by the backend and displayed in the registered-anatomy view. It does not turn the procedural landmark schematic into validated anatomy. Correct deep nuclei, white-matter structures, veins, pituitary, brainstem subdivisions and spinal/optic models remain required work.

`neuroradiology-atlas-scope-review/mapping-correction.json` records the original and corrected selections against the actual manifest names. Desktop/mobile browser checks confirmed that the genuine ventricular step still highlights its four ventricular meshes and switching to deep grey matter clears those highlights while showing the missing-anatomy note. The mobile view has no horizontal overflow. Fifty-one relevant tests and JavaScript syntax checks passed.

The shared-reader dependency hashes for pending MSK source assets were updated after checking that the only shared JavaScript change is the optional note display. Their meshes, figures, selection controls and anatomical-review statuses remain unchanged; no clinical approval was granted. Current MSK audit: `msk-verification-reader-notes-2026-09-30.json`. The all-radiology scope and audit were regenerated for the changed walkthrough contracts.
