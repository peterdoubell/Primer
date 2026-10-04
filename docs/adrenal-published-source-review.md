# Original adrenal CT/MRI source figures

Ten complete figures from Albano et al., *Imaging features of adrenal masses* (2019), are now available in the local adrenal reader. The source article and original XML grant CC BY 4.0: [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC6349247/), [DOI](https://doi.org/10.1186/s13244-019-0688-8). These are actual published imaging examples, not generated anatomical substitutes.

Original NLM/PMC metadata, XML, media and PDF snapshots were acquired separately. XML, PDF and each selected repository figure pass the publisher's per-file MD5. Larger original PDF image objects are retained: Figure 5 and Figure 7 JPEG streams match the PDF bytes exactly; the other eight figures use lossless PNG containers whose every image sample matches independent decoding of the original PDF object. Original page/object identities, encoded and decoded hashes, source colour-space/profile facts and panel maps are retained in the [source proof](adrenal-published-source-review/original-source-review.json). No crop, resampling, tissue repair, annotation change or fabricated enhancement was applied. Figure 8 retains original RGB samples; display/ICC calibration remains unverified.

| Figure | Selected modality/panels | Separate panels | Source-described example |
| --- | --- | --- | --- |
| 1 | MRI B/C | CT A | Adenoma and chemical-shift comparison |
| 2 | MRI A–D | — | Bilateral nodular hyperplasia; sequence-label ambiguity retained |
| 3 | CT A/B | — | Right adrenal haemorrhage |
| 4 | MRI A–C | — | Right adrenal cyst |
| 5 | MRI B–E | CT A | Left myelolipoma and composition |
| 6 | MRI A–C | — | Bilateral phaeochromocytoma, source MEN2 context |
| 7 | CT A–C | — | Right haemangioma and contrast comparison |
| 8 | MRI B–D | Ultrasound A | Source cortical carcinoma with heterogeneous components |
| 9 | CT A–C | — | Left lymphoma and separate bowel context |
| 11 | MRI C–F | CT A/B | Left breast-cancer metastasis and diffusion/enhancement comparison |

Figure 10 is excluded because its caption credits an external Nuclear Medicine Service database; the article-level grant is not treated as proof of separate credited-media permission. Figure 2's caption labels opposed-phase imaging C and later B while also naming T2 C. The original caption and visible panels are preserved, with the ambiguity disclosed rather than repaired or used for precise sequence credit.

Source diagnoses, field/sequence/phase descriptions and arrows remain author claims. The 2019 article contains older management and washout statements; the reader explicitly treats these figures as imaging context, retaining the separately named current clinical frameworks. MRI, CT and ultrasound panels cannot lend each other signal, endocrine function or diagnostic certainty. None supplies original calibrated DICOM, complete fine gland/limb/capsule/cortex/medulla, full lesion/vessel boundaries, tumour thrombus, native acquired master resolution or patient-specific 3D geometry. Figure attachments are not counted as independent cases or approved structure coverage.

[Packaging evidence](adrenal-published-source-review/packaged-source-images.json) binds all ten local files. Their licensing records carry attribution and exact evidence hashes; every structure binding remains empty and anatomical review remains pending. All ten source figures were reviewed together in a contact sheet for complete panel layouts, and Figure 11 was directly inspected at its preserved resolution. This source presentation review is not independent specialist approval.

Verification: 198 focused source/scope/reader/illustration checks passed. Local API delivery and every served file hash were verified. Browser checks loaded all ten at preserved dimensions on desktop 1440×1000 and mobile 390×844, with no page overflow or page errors; full-size Figure 11 opens at 1183×1784. Final mobile/desktop presentation, attribution and modality captions were directly inspected. The initial lazy-loading decode observation was resolved by checking actual load completion, without changing asset pixels. The owned browser and local server were closed after verification.

Reproduction uses the original PMC6349247.1 metadata/XML/PDF under the ignored source root, `pdfimages -png -j` to preserve/extract the PDF image objects, then `tools/anatomy_sources/acquire_adrenal_published_figures.py` with `--source-root` and `--output`. Acquisition requires Pillow and pypdf; the packaging tool requires the verified proof and original extracted files. Raw source snapshots remain outside runtime and version control. No clinical approval, model promotion, full-module readiness or production deployment is claimed.
