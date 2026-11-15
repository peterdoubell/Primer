# Hepatic source vessel navigation

The Liver lesson, liver-mass reporting and LI-RADS reporting now provide four direct, scoped links to original ColonVessels pat_012 CT labels and their exact boundary models. Each opens the requested source layer/value and returns to the initiating lesson or report. The MRI region study remains a separate case; the UI explicitly states that the CT and MRI come from different people and are not registered.

| Reference | Phase | Source layer:value |
|---|---|---|
| Common hepatic artery | Arterial | 1:4 |
| Right branch of proper hepatic artery | Arterial | 1:1 |
| Left branch of proper hepatic artery | Arterial | 3:2 |
| Portal vein | Venous | 2:7 |

`bindings.json` preserves exact source names, model hashes and triangle counts. The original source has in-progress annotation tags; the venous terminology tags also contain an unrelated costal-cartilage code. The source viewers retain those discrepancies and review limitations. These links are source-reference candidates, not independent anatomical validation.

## Remaining requirements

The portal vein is one source label. Neither its individual segmental branches nor hepatic veins or bile ducts are separately labelled in this study. The arterial names do not establish every accessory/replaced artery, arterial wall interface or segment-specific supply. The separate liver MRI supplies eight region annotations, with a single IV label rather than IVa and IVb. No cross-person registration or assignment of these CT vessels to the MRI regions is inferred. Lesion enhancement, tumour in vein and other pathological reporting findings require separate evidence.

The liver-mass and LI-RADS inventories retain all 246 and 210 structure/interface requirements, respectively, each requiring images, schematics and models. This navigation change does not approve those requirements or change their evidence status.

## Verification

The authenticated local reader check follows all four links from each of the three entry points, checks the selected source layer/value, compares actual GPU buffers with the source hashes and follows every scoped return link. Existing delivery and historical-compatibility tests remain in force. `runtime-inverse.json` limits shared-reader compatibility normalization to the exact navigation edit.

## Read-only production check

`tools/check_hepatic_vessel_production.cjs` accepts a JSON fixture on stdin with `url`, `username` and `password`. The origin is fixed to Primer production and browser requests are restricted to GET on that origin. It does not create a profile or change learner data. Supply credentials through a private pipe, never command-line arguments or a committed fixture. The checker compares the deployed reader and vessel delivery files with `production-files.json`, then follows all twelve paths and verifies selected labels and actual GPU buffers. A changed production reader requires an explicitly reviewed update to the pins.
