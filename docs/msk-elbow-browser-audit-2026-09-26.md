# Elbow source-figure browser audit — 26 September 2026

**Passed: all eight elbow records on the actual `#/radiology/ra.mri-elbow` reporting desk.** This is rendering and interaction evidence, not anatomical fidelity or clinical approval. No source pixels, application code, requirements or ledger records were changed.

The isolated server used `/tmp/primer-elbow-figures-qa.Xaw1SS/reader.db` on port 8803. Startup was checked with the browser verification skill; the focused run used `tools/check_msk_atlas.cjs --elbow-only`. The owned server and browser session were stopped after inspection.

## Results

- All eight local image responses matched their recorded SHA-256 and native dimensions; browser decoding and full-size decoding succeeded.
- Images contains six clinical-image records (four MRI and two Ultrasound); Diagram contains two schematic records. The biceps-attachments composite is labelled `Schematic + dissection panels`, with separate a–d dissection observations and panel-e overlay scope.
- Every caption, attribution, license link and stated limit matched the current catalogue. The six new records retain expandable full source captions; keyboard opening/closing was verified where the complete caption differs from display text.
- Enter opens each image, the full-size control retains native dimensions, and Escape restores focus. Desktop and 390-pixel mobile screenshots were captured, with no horizontal page overflow.
- Neither clinical pane contains generated contextual photographs. The reporting guide retains its own checklist and exact override.
- No uncaught browser errors or failed local source-image requests occurred.

## Actual pixel inspection

| Figure | Native pixels | Browser observation |
|---|---:|---|
| open-elbow-ligaments-fig4 | 1418×715 | A/P/T-MCL and RCL/LUCL/AL source labels intact. |
| open-elbow-lateral-ligaments-mri-fig7 | 1418×1518 | Four MRI panels retain arrows, asterisks and LE/SC labels. |
| open-elbow-anterior-ucl-mri-acosta-fig5 | 1418×700 | All three panels retain ME, stars, arrowheads and striation arrows. |
| open-elbow-posterior-ucl-ulnar-nerve-mri-acosta-fig6 | 1418×574 | White arrows/arrowhead, yellow nerve stars and white variant star visible; caption distinguishes two volunteers. |
| open-elbow-triceps-insertion-mri-valgaeren-fig2 | 1511×838 | CMYK source renders readable a/b panels and yellow arrows without apparent color inversion. |
| open-elbow-common-flexor-ultrasound-mezian-fig6a | 716×416 | Native panel a retains CFT, ME, distal label and scan scale; omitted pathology panels stay excluded. |
| open-elbow-distal-biceps-ultrasound-mezian-fig10a | 683×414 | Native panel a retains DBT, brachialis and distal labels; no complete footprint claim. |
| open-elbow-biceps-attachments-mezian-fig8 | 2017×1152 | a–d dissection and e attachment-overlay labels/markers intact; separate coverage paragraphs preserve the distinction. |

The Valgaeren source remains a CMYK JPEG at **1511×838**. Browser canvas sampling found **6453 yellow pixels**, with black and mid-gray MRI detail present. Desktop and mobile inspection showed preserved arrows, grayscale and caption limits. The stored source was not converted; browser color management performs display decoding.

## Exact artifacts

Browser evidence and screenshots: [/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/results.json](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/results.json). Useful views:

- [CMYK triceps MRI](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/ra.mri-elbow-open-elbow-triceps-insertion-mri-valgaeren-fig2-clinical-image-desktop.png)
- [Common-flexor ultrasound at native size](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/ra.mri-elbow-open-elbow-common-flexor-ultrasound-mezian-fig6a-clinical-image-native-zoom.png)
- [Biceps dissection/overlay scope](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/ra.mri-elbow-open-elbow-biceps-attachments-mezian-fig8-schematic-desktop.png)
- [Distal-biceps ultrasound on mobile](/var/folders/kq/2zbgq4xj5wb5rrs65kysm2f80000gn/T/primer-browser-qa-liMdLt/ra.mri-elbow-open-elbow-distal-biceps-ultrasound-mezian-fig10a-clinical-image-mobile.png)

Source bytes checked:

| Asset ID | SHA-256 |
|---|---|
| open-elbow-ligaments-fig4 | `3d4189bfd3ca45f47df754e6108dcffa6ae7746564cf5fed7dbc8ba43d139888` |
| open-elbow-lateral-ligaments-mri-fig7 | `a50f8bf989f02a5661e00334c4ca5ada63ba599dde04e31f8753cabde3348523` |
| open-elbow-anterior-ucl-mri-acosta-fig5 | `49013fddddc3d3602199ada0691fe639151269a88601085975a90171b89fa2f8` |
| open-elbow-posterior-ucl-ulnar-nerve-mri-acosta-fig6 | `dca2cc27c859d89bf91407d05992acade8623bc9884e753d649608e3dd9e41bc` |
| open-elbow-triceps-insertion-mri-valgaeren-fig2 | `cd986d53c8bc2463fc2d089da1893dee7ec33461b87e09190fd034967373ca88` |
| open-elbow-common-flexor-ultrasound-mezian-fig6a | `83d7587e17f069d956ecf8927254abfb0abb1240abbd903746625378d868cc3e` |
| open-elbow-distal-biceps-ultrasound-mezian-fig10a | `efc545268145ac14888549ec00a81c5615c9cc980e004908c3e4f289742d21be` |
| open-elbow-biceps-attachments-mezian-fig8 | `1e36683fc070e1eccd9b42c36b35b6a2ac464a950370b12b97572cdd5a505947` |

Served application/viewer/style/atlas hashes matched the workspace and remained unchanged through the run:

```json
{
  "app.js": "ab7c765de74350c09569ad4204585108baa86bba814ae8398de4d98f00292e25",
  "styles.css": "948a1f35f1b249f82b4383b3329ee3dca6149fafa005b70c3d8b11fcef9e01ee",
  "radiology-detailed-anatomy.js": "00f7f8066f1c8a0f2309581681766b044641a1e348c85c5776f17babfd62100a",
  "anatomy/msk-atlas/manifest.json": "ef50083f82c062154d13b91cb3f672cf28fabd02bdc835c67dc1c5814f1d335c"
}
```

Source provenance and acquisition limits remain in [the elbow acquisition record](msk-elbow-image-progress.md). In particular, the ultrasound panels do not establish MRI visibility, the dissection photographs are not MRI/US evidence, and the insertion overlay does not provide a measured enthesis or a new clinical approval.
