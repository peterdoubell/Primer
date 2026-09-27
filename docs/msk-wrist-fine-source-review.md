# Wrist fine-component source decisions

The bounded source pass of 26 September 2026 added **no runtime asset or evidence binding**. This consolidation, checked against the available primary files on 27 September, preserves that result. The existing eleven wrist records and all component requirements remain unchanged. No clinical approval, contact, new search or access retry was made.

The target was complementary normal MRI/MRA or an authored schematic for the ECU subsheath/fibro-osseous tunnel or finer meniscal-homologue/ulnocarpal relationships. A broad TFCC illustration does not by itself fill those gaps. The unchanged [acquisition log](msk-source-followup-review/wrist/acquisition-log.json), empty [final records](msk-source-followup-review/wrist/final-records.json) and empty [proposed bindings](msk-source-followup-review/wrist/proposed-bindings.json) preserve the previous pass; the [source-quality review](msk-source-followup-review/wrist/source-quality-review.json) records the independent checks and qualifications below.

| Candidate | Supported source decision |
|---|---|
| [Gupta et al. 2018, Figure 3](https://doi.org/10.7759/cureus.2489) | The preserved primary XML gives an article-level CC BY 3.0 license but expressly says Figures 3 and 4 were used with permission from MRI Web Clinic–Radsource. That borrowed-image permission does not establish an onward commercial sublicense. Exclude the figures; no image imported. |
| [Khalilzadeh, Canella and Fayad 2021, Figure 4.19](https://doi.org/10.1007/978-3-030-71281-5_4) | The chapter explicitly includes third-party images in CC BY 4.0 unless a contrary credit indicates otherwise. No contrary restriction was found for this figure. The inspected primary PDF page 53 shows schematic panel a and one coronal MRI panel b. It adds no material ECU-tunnel/retinaculum relationship beyond the prior wrist scope; do not promote it. The schematic ECUS/UL/UT labels cannot earn MRI-only component credit. |
| [JCDR 2022, Table/Figure 2](https://doi.org/10.7860/JCDR/2022/59277.17323) | The saved [publisher license statement](https://www.jcdr.net/aboutus.aspx) expressly applies CC BY-NC-ND 4.0. Exclude from the commercial collection; no image imported. The consolidation verifies rights, not new figure-level coverage. |
| [Mespreuve et al. 2015, Figure 2](https://doi.org/10.5334/jbr-btr.846) | Original primary XML verifies CC BY 3.0 and the normal TFCC/homologue caption. Prior pass declined the overlapping coverage. It also recorded a [published correction](https://doi.org/10.5334/jbr-btr.966); that correction's original is not in this cache, so its exact contents are not newly verified or used as definitive evidence. No import. |
| [Campbell et al. 2013](https://doi.org/10.1136/bjsports-2013-092835) | Prior pass recorded CC BY-NC 3.0 and excluded it. No primary Campbell file is available in this bounded cache, so that rights result remains prior-pass reporting rather than a newly verified claim. No import or credit is proposed. |

A mere contributor or courtesy credit is not itself a restriction. Gupta's figure-specific **used-with-permission** language is the relevant distinction; Springer’s express inclusive image license remains applicable absent contrary wording. The Springer decision is based on insufficient additional coverage, not a presumed rights exclusion.

## Corrected Figure 4.19 caption

The saved [formal Springer correction of 21 July 2023](https://doi.org/10.1007/978-3-030-71281-5_22) changes Figure 4.19(b) marker **2 to distal lamina** and marker **4 to proximal lamina**. The current saved publisher HTML and PDF already reflect those labels. Source numbers and pixels were not altered. Any future use must carry the corrected caption and correction reference.

The prior audit reported the opposite assignments on NCBI Bookshelf. However, its saved `wrist-hand2021-ncbi-figure.html` is a reCAPTCHA challenge response, not a figure-caption capture. That file cannot independently establish NCBI's displayed labels. The formal publisher correction is sufficient to establish the corrected mapping; no NCBI retry was made.

## Durable evidence

[Preserved evidence](msk-source-followup-review/README.md) contains the unchanged acquisition records, small primary article XMLs, and bounded exact text extracts from the saved publisher caption, license and correction pages with their original SHA-256 fingerprints. All source/review hashes in the wrist acquisition log matched the staged files during consolidation. Large PDFs, rendered pages and image archives remain outside the repository; no accepted asset was cropped, recompressed or substituted by an extract.
