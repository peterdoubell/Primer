# Shoulder source-image acquisition and inspection

Reviewed 2026-09-26. Six entries were added to `ra.mri-shoulder` in `data/radiology/msk-open-images.json`; the previous 36 entries remain unchanged. The base catalog now contains **42 unique entries**, including separately preserved source panels. Shared placements in other investigations are not new acquired figures. Source acquisition itself did not edit the ledger or requirements. Subsequent integration added seven representation records with local candidate bindings, explicit source context and pending clinical reviews.

The ultrasound-shoulder reference now reuses only the Xue ultrasound panel,
Kadi interval schematic and Perez footprint schematic. The selective-sharing
configuration preserves their original metadata, avoids copying MRI scans into
that selected source gallery, and leaves the ultrasound report unchanged. The
ultrasound clinical-image evidence is bound only to the ultrasound investigation;
its local reference does not establish full dynamic stability or footprints.

## Acquired normal anatomy

| Entry | Original pixels | What is visibly identified | Important boundary |
|---|---:|---|---|
| `open-shoulder-normal-interval-mri-kadi-supp-fig3b` | 1370×1267 | Native sagittal oblique 3 T PD MRI: labels 16 subscapularis tendon, 18 LHBT, 27 supraspinatus, 14+28 infraspinatus muscle/tendon, 38 SGHL, 44 CHL. The source also labels local CAL, subacromial bursa, MGHL, IGHL/capsule and surrounding anatomy. | One slice. Label presence does not establish complete courses, individual pulley bundles or tendon-footprint borders. Supplemental panel B only; the full three-panel caption is retained separately. |
| `open-shoulder-rotator-interval-kadi-supp-fig6` | 1111×1093 | Original sagittal schematic labels supraspinatus and subscapularis muscle/tendon, LHBT, CHL, SGHL and humeral head. | Schematic relationships only. No MRI validation, measured footprint or 3D registration. Original A.M. initials preserved. |
| `open-shoulder-supraspinatus-components-perez-fig1` | 958×2479 | MRI panels b/c label anterior and posterior supraspinatus bellies; solid arrows identify anterior tendon/insertion and a dashed arrow the broader posterior tendon. Panel a is the corresponding signed drawing. | Clinical `structures_visible` is confined to b/c. Drawing coverage is separately recorded. No complete cuff footprint or other cuff-tendon insertion claim. |
| `open-shoulder-cuff-footprints-perez-fig2` | 893×855 | Signed superior humeral-head drawing: SS orange and IS brown insertion zones, with intact legend. | Schematic supraspinatus/infraspinatus footprints only. No subscapularis/teres-minor footprint, subject-specific dimensions or MRI claim. |
| `open-shoulder-subscapularis-insertion-mri-perez-fig5` | 893×1795 | Normal MRI a outlines the comma-shaped subscapularis insertion; MRI b has two arrows along the tendon. | Two source MRI sections, not a complete series. Educational outline is not independently measured enthesis segmentation or proof of every attachment subregion. |
| `open-shoulder-rotator-interval-ultrasound-xue-fig1b` | 816×446 | Native ultrasound panel B: labels 1 LHBT, 2 CHL at three positions, 3 SGHL, 4 subscapularis tendon, 5 supraspinatus tendon, 6 deltoid. | Ultrasound, **not MRI evidence**. Local transverse interval example only, not a dynamic examination. Native resolution is retained; patient-position photograph A is omitted. |

The selected primary figure captions and section placement describe normal anatomy; pathology examples from the same review papers were not substituted. Source laterality is not explicitly stated for these examples and was not inferred. “Figure S3b” and “Figure S6” are display labels identifying Kadi's **additional material**, not main-text Figures 3 and 6.

## Primary sources and rights

1. **Kadi, Milants and Shahabpour (2017), Shoulder Anatomy and Normal Variants**, [primary deposited article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6251069/), [DOI](https://doi.org/10.5334/jbr-btr.1467), [additional material](https://pmc-oa-opendata.s3.amazonaws.com/PMC6251069.1/jbsr-101-2-1467-s1.pdf). The article's PDF and publisher-deposited JATS specify CC BY 4.0. The JATS identifies the supplement as the article's additional material with DOI `10.5334/jbr-btr.1467.s1`. Selected supplemental captions/images have no different license or restrictive reuse notice. The drawing's A.M. initials remain intact; no unverified full illustrator identity was invented.
2. **Perez Yubran et al. (2024), Rotator cuff tear patterns: MRI appearance and its surgical relevance**, [publisher article and rights statement](https://link.springer.com/article/10.1186/s13244-024-01607-w), [Figure 1](https://link.springer.com/article/10.1186/s13244-024-01607-w/figures/1), [Figure 2](https://link.springer.com/article/10.1186/s13244-024-01607-w/figures/2), [Figure 5](https://link.springer.com/article/10.1186/s13244-024-01607-w/figures/5). The publisher explicitly includes images and other third-party material in CC BY 4.0 unless a credit line indicates otherwise. None of these captions/images states a different license or restriction. The illustrations retain **M. Crespi ©**; the article acknowledges **Massimiliano Crespi**. This is an artist attribution, not an exclusion, and is preserved in both pixels and text. The author contributions identify the authors as image providers.
3. **Xue, Bird, Jiang, Jiang and Cui (2022), Anchoring Apparatus of Long Head of the Biceps Tendon: Ultrasonographic Anatomy and Pathologic Conditions**, [publisher article](https://www.mdpi.com/2075-4418/12/3/659), [primary deposited article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8947553/), [publisher-deposited PDF](https://pmc-oa-opendata.s3.amazonaws.com/PMC8947553.1/PMC8947553.1.pdf). Publisher-deposited JATS and PDF specify CC BY 4.0, © authors. The exact Figure 1 caption and clinical panel B carry no separate restrictive credit. Only the embedded ultrasound panel is retained.

All six permit commercial redistribution under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) with attribution, license notice and change disclosure. Attribution records contain all named article authors, the original source caption, original asset URL, dimensions, file SHA-256, acquisition details, and exact panel limits. Commercial reuse of these figures does not establish clinical validation of Primer's models.

## Correction to the earlier courtesy-credit assessment

The earlier acquisition notes treated Kadi main Figures **14** and **15** as excluded solely because their captions say **“Courtesy of Dr Deepu Alex Thomas”** and **“Courtesy of Dr Henri Guerini”**, respectively. Reinspection of the exact main PDF captions and publisher-deposited JATS found **no explicit different license, noncommercial restriction, permission-only condition or exclusion** in those credit lines. Courtesy identifies a contributor; it is not itself a contrary license. The earlier categorical exclusion rationale is therefore unsupported.

Those two figures were not added in this bounded acquisition: they show sublabral foramen and Buford-complex variants and are less directly useful for the requested cuff-footprint/pulley gaps than the six selected normal figures. If later acquired, preserve the named courtesy credits and review the complete current figure context; do not label them restricted based on courtesy wording alone. No publisher or author was contacted.

## Native-pixel and annotation checks

- Kadi supplemental Figure 3B: PDF page 4, `Image25.jp2`, index 0. Supplemental Figure 6: page 7, `Image40.jp2`, index 0. Lossless JPEG-2000 decoding to PNG preserved mode, dimensions and every decoded pixel. Source/saved pixel hashes are recorded.
- Perez Yubran Figures 1, 2 and 5: the publisher figure pages' **full-size PNGs**, not thumbnail URLs. Original bytes, complete composites, panel letters, arrows, outlines, legends and artist signatures are preserved.
- Xue Figure 1B: PDF page 2, `Im6.jpg`, index 1. Original embedded JPEG bytes retained. All six numeric labels, repeated CHL label-2 marks, depth scale and B label are part of the bitmap; no separately drawn PDF annotations were lost.
- Every selected image was viewed at its native available detail. No AI processing, painting, sharpening, resizing, upscaling or artificial reconstruction was performed. UI scaling does not add source detail.
- Staging evidence and before/after records are in `/tmp/primer-msk-sources/shoulder-batch/`; durable provenance and SHA-256 values are in the manifest and `web/reference-media/msk-open/ATTRIBUTION.md`.
- Fresh loader validation passed: 42 unique catalog entries, 53 placements including 11 existing shared wrist copies, and 9 shoulder entries. All 36 previous manifest records compare exactly equal to the pre-acquisition snapshot. All six new files passed hash and dimension checks; recorded decoded source/saved pixel hashes match. Browser presentation is a separate downstream check.

## Remaining concrete gaps

These figures supply local normal cuff and interval examples; they do not complete shoulder coverage. Missing proof includes a complete normal multiplanar series for each cuff footprint, precise teres-minor insertion margins, individual medial/lateral biceps-pulley bundles and their attachment coordinates, dynamic biceps stability, measured surface geometry and spatial registration between MRI and any displayed 3D model. The ultrasound example can support ultrasound teaching only. The schematic footprint borders must not be promoted to metric anatomy or clinical MRI evidence.
