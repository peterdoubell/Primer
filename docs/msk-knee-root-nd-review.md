# Unchanged CC BY-ND knee-root figure review

Reviewed 26 September 2026. **Two complete original JPEG figures are integrated in `ra.mri-knee`, unchanged.** This addition brought the source-image catalog from 59 to 61 unique entries. The actual license remains CC BY-ND 4.0, with original-byte and complete-figure checks enforced by the catalog loader. Two pending evidence records are prepared separately in `/tmp/primer-msk-sources/knee-root-nd-review/ledger-records.json` for the serialized ledger merge; this reconciliation did not write the shared ledger or global attribution file.

## Finding

The primary grant for [Wang et al., 2018, The imaging features of the meniscal roots on isotropic 3D MRI in young asymptomatic volunteers](https://pmc.ncbi.nlm.nih.gov/articles/PMC6392791/) is **CC BY-ND 4.0**, not a noncommercial license. The publisher-deposited JATS and PDF explicitly permit commercial and noncommercial redistribution when unchanged and credited. Exact complete Figures 6 and 7 have no separately credited restricted material, permission-only notice or figure-specific exclusion.

The [official license deed](https://creativecommons.org/licenses/by-nd/4.0/) expressly allows commercial sharing. [Legalcode §2(a)(1)](https://creativecommons.org/licenses/by-nd/4.0/legalcode.en) permits reproducing and sharing licensed material in whole or in part but does not permit sharing adapted material. The article's “unchanged and in whole” wording is preserved in `primary-license-grant.txt`; this planned use keeps each complete figure unchanged, including every panel, original arrow and panel letter. It does not rely on a right to distribute adaptations.

The planned use therefore meets the source's commercial-reuse requirement **under an unchanged-complete-figure distribution plan**. This is a source-license assessment, not clinical approval. An application must preserve attribution, copyright and license notices/link, source link, supplied notices and unmodified status; it must not imply endorsement or impose additional downstream restrictions/DRM that curtail licensed rights. Crops, added arrows, relettering, recoloring, reconstructions and altered panels are not proposed. Technical display scaling of the original file need not change the distributed source bytes. No resized/transcoded downloadable derivatives are supplied.

## Exact original assets

The two JPEGs in `web/reference-media/msk-open/` are byte-for-byte copies of the original standalone figure files obtained through the NLM PMC Open Access publisher-deposited media URLs. Their staging originals remain in `/tmp/primer-msk-sources/knee-root-nd-review/assets/`. **No figure was extracted from the PDF**, so no separately drawn PDF vectors or panel markers could have been lost.

| Figure | Complete native file | Original MD5 from NLM metadata | SHA-256 |
|---|---|---|---|
| 6 | `knee-lateral-posterior-root-wang-2018-fig6.jpg`, 800×489, 85,095 bytes | `d590b6145a41163f5e8b5f8cac135d06` | `0066da065d52d1af7a1bd945fae3d75208833246598d1923a51986e738deae68` |
| 7 | `knee-lateral-posterior-root-wang-2018-fig7.jpg`, 800×984, 145,340 bytes | `5e96d5db4cbdac2d55d869572e749a2d` | `bf212b49ecffe5b9a5f3befd2807e1b7cf6b598a9e281adf07192b6c3a0a845b` |

The authoritative machine-readable digests are in `data/radiology/msk-open-images.json`. Retrieved bytes match the supplied NLM MD5 values, and integrated bytes equal retrieved bytes. Both JPEGs decoded and were visually inspected as complete figures at native detail. Figure 6 retains A/B and both white arrows. Figure 7 retains A/B/C/D and the thick/thin arrows marking major/minor components. No files were cropped, recompressed, upscaled, painted, sharpened or reannotated.

## Anatomy and context

- Figure 6: coronal A and sagittal B show the posterior root of the lateral meniscus, marked by white arrows. The caption describes a single hypointense bundle inserting along the intertubercular fossa. This supplies a local candidate for `knee.lateral_meniscus.posterior_root` only.
- Figure 7: posterior/anterior coronal A/B and lateral/medial sagittal C/D show major and minor lateral posterior-root insertion components. The complete figure is preserved; no panel is selected for separate distribution. Same single requirement candidate; the two examples are not two independently validated structures or complete volume coverage.
- Primary methods: 60 knees from 31 asymptomatic volunteers, aged 20–23; no knee symptoms or history of injury, infection, synovitis or arthritis. MRI was acquired in vivo at 3 T with fat-suppressed isotropic 3D PD-SPACE, 0.6-mm voxels. Figure-specific exact age, sex and side are not stated. No individual demographic values are invented from the cohort average.
- The authors explicitly caution that the image-based bundle classification may not reflect true anatomical constitution. These figure examples do not supply the original full MRI dataset, anatomical dissection validation, independently measured insertion surfaces or clinical certification.

## Previous exclusion and integration boundary

No explicit **user** instruction or applicable project policy forbidding commercial unchanged CC BY-ND figures was found. Earlier delegated source-acquisition briefs for other bounded batches used “exclude NC/ND”; that sourcing filter was carried forward too broadly into the knee note. The current instruction expressly replaces that blanket criterion with exact commercial-use and unchanged-figure review. The earlier claim that a user-required unrestricted-modification/no-ND policy prevented these figures was unsupported and has been corrected in the knee source audit. CC BY-ND must not be confused with CC BY-NC-ND.

The catalog loader now has an exact `CC BY-ND 4.0` name/URL entry and requires the unchanged-complete-figure use plan, complete panels, original-byte preservation, a matching source SHA-256 and matching source MD5. **The figures are not relabeled CC BY.** Commercial redistribution is permitted, distribution of adapted material is not, and the existing clinical/anatomical gates remain unchanged. Technical preservation conditions are distinct from clinical approval.

The provenance package remains at `/tmp/primer-msk-sources/knee-root-nd-review/`: original metadata, XML/PDF, primary grant, unmodified source JPEGs, attribution and two local ledger records. Each ledger record binds only `knee.lateral_meniscus.posterior_root`, includes all original MRI panels, has `depicted_state: normal_anatomy`, adult cohort age range 20–23, and unknown individual age/sex/side. No average age or individual identity was inferred. Visual status is `source_checked`; anatomical/clinical approval remains pending.

## Attribution correction and fragment verification

Primary JATS contributor types identify **seven authors**: Ping Wang, Cheng-Zhou Zhang, Di Zhang, Quan-Yuan Liu, Xiao-Fei Zhong, Zhi-Jie Yin and Bin Wang. **Weisheng Zhang is the academic editor**, not an eighth author. The initial staging script selected every contributor name; the corrected fragment and local attribution now filter `contrib-type="author"`. The parent task was supplied `attribution-correction.txt` for the two integrated image attributions and the shared attribution file. This corrects role attribution without changing pixels, licensing or anatomical scope.

The two local ledger records passed exact integrated/source-byte comparison, original MD5/SHA-256, native dimensions, source-context type checks, requirement/modality matching and rights-evidence checks. Neither receives approval: the existing fidelity gate still reports high fidelity unproven and anatomical review pending. At fragment validation, the shared ledger contained 667 rows after the separate hip merge; a non-writing simulation with the two records produced 669 rows and changed **0 verified / 129 unverified / 5073 missing** to **0 verified / 130 unverified / 5072 missing**. Both records address the same one representation requirement, not two distinct coverage leaves. The actual shared-ledger merge remains serialized by the parent task.
