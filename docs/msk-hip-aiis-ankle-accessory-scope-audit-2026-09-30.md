# Hip AIIS and MRI-ankle accessory-muscle scope audit

Reviewed 2026-09-30. This is an additive proposal, not an applied requirement correction or an anatomical approval. The exact field snapshots, file hashes, proposed IDs and count validation are in [the proposal JSON](msk-hip-aiis-ankle-accessory-scope-proposal-2026-09-30.json).

Two omissions are proven by the current repository-authored walkthrough. The broader worksheets remain intact.

| Investigation | Current exact walkthrough finding | Inventory omission |
| --- | --- | --- |
| `ra.hip-fai` | Step 4, finding 0: “Prominent anterior inferior iliac spine extending to the acetabular rim (subspine impingement morphology).” | None of the 20 structures or 50 component parts names the AIIS or subspine region. Acetabular rims and femoral head/neck already exist and are preserved. |
| `ra.mri-ankle` | Step 4, finding 3: “Accessory muscle: [peroneus quartus / accessory soleus / flexor digitorum accessorius longus].” | None of the 48 structures or 158 parts names these three variants. The existing affected-muscle expansion rule has an empty `named_sites_or_targets` list; that generic rule is insufficient to prove these explicit targets are instantiated. |

The hip worksheet's alternative-pain-generator section already permits additional osseous findings. The ankle worksheet already permits a muscle or soft-tissue lesion. Adding anatomy targets does not require deleting, replacing or narrowing either field. The walkthrough is the direct evidence for the named omissions; no accessory muscle was added merely because it could exist.

The AIIS proposal adds `hip.anterior_inferior_iliac_spine`, with two independent bone-surface targets: `inferior_prominence` and `subspine_region`. The original CT study evaluates caudal AIIS morphology against the acetabular rim. These two targets preserve that local distinction without treating an entire hip bone as component proof. [Hetsroni et al., original CT study](https://link.springer.com/article/10.1007/s11999-013-2847-4).

Acquisition limits remain explicit. An AP projection can show a prominence but does not reliably establish the full 3D morphology. CT/MRI evaluation depends on actual coverage and suitable bone acquisition; static morphology does not independently establish symptomatic or dynamic impingement. [Original AP-versus-3D evaluation](https://pubmed.ncbi.nlm.nih.gov/28432458/).

The ankle proposal adds exactly the three named muscles. Each receives four coverage-qualified component targets: observed belly, visible musculotendinous course, individual proximal attachment if covered, and individual distal attachment if covered. These are anatomy decompositions requiring specialist review. They do not impose a universal accessory attachment, require that an accessory muscle exist in every examination, or erase the existing rule for any other affected named muscle.

- `ankle.peroneus_quartus_muscle`: keep it distinct from usual fibularis longus/brevis and fibularis tertius. An original MRI series separately evaluates the accessory muscle and adjacent peroneal tendons. [Yuksel et al., original 1160-examination study](https://pubmed.ncbi.nlm.nih.gov/41008701/).
- `ankle.accessory_soleus_muscle`: preserve the individual's captured attachment rather than substituting usual soleus. Original cadaver/MRI work records different attachment patterns. [Original cadaver and MRI study](https://pubmed.ncbi.nlm.nih.gov/21538570/).
- `ankle.flexor_digitorum_accessorius_longus_muscle`: retain the captured course and relationship to the existing tarsal-tunnel structures. Original specimen and MRI/surgery reports support reviewing the accessory structure separately. [Cadaver report](https://pubmed.ncbi.nlm.nih.gov/9232504/), [MRI/surgical case](https://www.jstage.jst.go.jp/article/nmccrj/11/0/11_2023-0136/_article). The latter publisher marks its media CC BY-NC-ND; it is a factual reference only, with no media imported or adapted.

Each side remains separate. “Absent,” “not seen,” and “outside acquisition coverage” must not be collapsed into one state. A source showing no accessory muscle cannot be converted into a variant-positive mesh. Named targets are fixed; their observed presence, captured extent and attachments remain examination/exemplar specific.

No explicit new-target binding exists in the current evidence ledger. The hip inventories contain whole right hip bones (`za-bones-83785534`, `FJ3152`) but no named AIIS subobjects. The 147-part Z-Anatomy ankle inventory and 20-part Malaya MRI ankle inventory contain usual fibularis/FDL/soleus objects; they do not name the three accessory variants. Existing rectus-femoris Figure 2 is bound only to local tendon course. Neither a familiar muscle name nor a whole bone establishes the proposed components. Incidental visibility in currently unreviewed image panels remains unresolved.

Counts were computed using the actual `requirements_for` function in `tools/check_msk_fidelity.py`: listed children are targets, and the parent is counted only when it has no children. Hip would gain 2 targets and 6 representation obligations; MRI ankle would gain 12 targets and 36 obligations. Across the unchanged 22 investigations, the total would increase from **5,250 to 5,292** if this proposal alone were applied. The 42 additions preserve conditional scope and require image, schematic and model evidence independently. No asset binding, coverage waiver or clinical approval was assigned.
