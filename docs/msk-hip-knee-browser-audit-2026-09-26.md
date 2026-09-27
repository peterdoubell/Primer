# Hip, knee and Open Knee(s) browser verification — 26 September 2026

**Passed on actual reporting routes:** `ra.mri-knee` and `ra.hip-fai`. This verifies rendering, source transport and interactions; it does not grant anatomical fidelity, measurement accuracy or clinical approval. Only QA checker/document files changed during this pass.

An isolated database at `/tmp/primer-hip-knee-qa.Ep2g1s/reader.db` served port 8804. Startup was verified with agent-browser. The owned server and browser sessions were stopped after the checks.

## Source figures and report scope

`tools/check_msk_atlas.cjs --hip-knee-only` exercised all **17 current source records** (10 knee, seven hip), including all 13 newly added figures. Wu Figure 1 appears in both image and diagram panes, producing 18 tested pane placements.

- Every displayed original matched its recorded native dimensions and SHA-256. Both CC BY-ND figures additionally matched their original NLM MD5 and source SHA; complete panel layouts, arrows and notices remain intact.
- Exact modality/version labels, source captions, attribution, license links and stated limits matched the current catalogue. The Aubry references retain MR arthrography and CC BY 2.0 labels.
- Wu Figure 1 separates MRI b, dissection a, and schematic c/d observations. The source-caption typo remains disclosed rather than turning a dissection into MRI.
- Amin Figure 3 retains the complete bilateral/mixed original: only the left panel-a arrowhead is described as the intact comparator. The right pathology is visible and explicitly excluded from a normal-anatomy claim.
- Enter opens each image; full-size mode retains native image dimensions; Escape restores focus. All records were checked on desktop and at 390-pixel mobile width with no horizontal page overflow. No synthetic contextual photographs appeared in the clinical panes.
- The actual hip guide and report template match the corrected override. A separate focused check confirms compatible symptoms, examination signs and imaging findings; the periarticular soft-tissue row is conditional on acquired MRI. The former mandatory labral/cartilage-injury statement is absent.

All 13 new figure screenshots were visually inspected, including native source arrows, labels, mixed panels and mobile presentations. No source metadata or rendering defect was found.

## Open Knee(s) provider

`tools/check_openknee_browser.cjs` selected `openknee-oks003` through the actual knee source selector; the original `malaya-mri` default remains unchanged.

| Check | Observed result |
|---|---|
| Lazy initial load | Four bone meshes only |
| Source objects | 16 unique controls and actual isolated renders |
| Geometry count | 307,024 facets |
| HTTP transport | All 16 gzip responses decoded to BP3D with exact byte length, vertex/index count and decoded SHA |
| Layers | Bones 4; cartilage 4; menisci 2; ligaments 4; tendons 2; every layer rendered nonzero pixels |
| Isolation | All 16 source objects rendered independently; selected menisci/cartilage/ACL also inspected on mobile |
| Left-side presets | Lateral yields Left lateral; Medial yields Right lateral; Anterior and Superior labels correct |
| Controls | Keyboard rotation, reset, Full structures and regional crop states passed |
| Source switching | UM → OpenKnee → UM → Z-Anatomy → OpenKnee; each old WebGL context disposed, exactly one provider mounted |
| Raw research imaging | No raw MRI/mask files in the static web tree and no raw-volume requests |

The current source notes visibly preserve the female, 25-year-old cadaveric left specimen, native RAS coordinates, separate-source framing, sampling/processing limits, missing component delineations and CC BY-SA 3.0 Unported attribution. Default/Together views, meniscal and cartilage isolates, and mobile ACL were visually inspected. No blank layer or mixed-source overlay was observed. Source self-intersection, exact tissue boundaries, attachment fibres and clinical completeness are outside this engineering pass.

## Evidence and exact source freeze

- [Figure results](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-fzH9ee/results.json)
- [OpenKnee transport/control results](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-zzseGU/results.json)
- [Explicit hip guide check](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-d61Ws2/results.json)

Useful inspected screenshots:

- [OpenKnee assembly](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-zzseGU/openknee-together-desktop.png)
- [Medial meniscus, superior view](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-zzseGU/oks003-mns-m-isolated-superior.png)
- [ACL on mobile](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-zzseGU/oks003-acl-isolated-mobile.png)
- [Unchanged lateral-root figure](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-fzH9ee/ra.mri-knee-open-knee-lateral-posterior-root-mri-wang2018-fig7-clinical-image-desktop.png)
- [Wu panel distinctions](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-fzH9ee/ra.mri-knee-open-knee-plc-anatomy-wu-fig1-clinical-image-panel-scope-desktop.png)
- [Mixed hip comparison](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-fzH9ee/ra.hip-fai-open-hip-gluteus-minimus-comparison-mri-amin-fig3-clinical-image-desktop.png)
- [MRI-conditional hip row](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-d61Ws2/hip-mri-conditional-row-mobile.png)

Served files matched the workspace before testing and remained byte-identical through the source freeze:

```json
{
  "app.js": "8c255a2a87be8c22a8777ab172607cce607d871c0e592cea4a5ee2c889d160b7",
  "styles.css": "948a1f35f1b249f82b4383b3329ee3dca6149fafa005b70c3d8b11fcef9e01ee",
  "radiology-detailed-anatomy.js": "6b7d76999ce797994c054664fde7919d0351323b4082fb213da1aaebd236c727",
  "anatomy/openknee-oks003/manifest.json": "c2617979ffafc90349f57174a083bd42410c2ab9f601e49200353a328afafcd4",
  "anatomy/msk-mri-knee/manifest.json": "728c4189e778cfbe9919e8769c89f02b3f22a5b277bd8a0a55a91a8066cc8061",
  "anatomy/msk-atlas/manifest.json": "ef50083f82c062154d13b91cb3f672cf28fabd02bdc835c67dc1c5814f1d335c"
}
```

The guide comparisons use parsed JSON values and actual rendered text, so an escape/UTF-8-only rewrite of `investigation-overrides.json` does not alter this evidence. No uncaught JavaScript exceptions, local source-image failures or WebGL errors occurred.
