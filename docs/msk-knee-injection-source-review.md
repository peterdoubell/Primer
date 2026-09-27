# Ultrasound knee-injection source review

27 September 2026. The current injection module has thirteen named target
groups, plus generic route-adjacent tendon, nerve, artery and vein requirements.
The knee group contains patella, femoral articular surface, the actual recess,
quadriceps tendon and capsule. Approach-specific instantiation remains required.

The [Radiology Assistant chapter](https://radiologyassistant.nl/musculoskeletal/ultrasound/us-guided-injection-of-joints)
explicitly describes its knee example as a technique without ultrasound.
Rechecked in the source's Knee section. It therefore cannot substantiate an
ultrasound needle-localisation example. The current reporting template's
ultrasound documentation fields remain appropriate to the module's stated
purpose; replacing them with that source's technique would change the purpose.
The existing source-scope issue remains unresolved.

A more specific source is Wu et al. (2024), *Ultrasound Imaging of the
Articularis Genus Muscle: Implications for Ultrasound-Guided Suprapatellar
Recess Injection*, DOI 10.3390/diagnostics14020183,
[PubMed record](https://pubmed.ncbi.nlm.nih.gov/38248060/).
The accessible abstract and captions identify articularis genus and its
relationship to the suprapatellar recess, quadriceps layers, vastus intermedius,
fat and bony landmarks. These support an approach-specific review proposal,
not a verified clinical representation or procedural recommendation.

The [machine-readable proposal](msk-knee-injection-scope-proposal.json) preserves
all existing knee parts and records six targets to examine against the full
source. Its fingerprint binds it to the current knee requirement definition.
It does not replace the other twelve target groups, waive neurovascular anatomy,
or turn an image caption into proof of a needle trajectory.

Full-text acquisition did not succeed: PMC and a later PubMed read returned
browser challenges, and the publisher resolver returned HTTP 429. Those
routes were not retried or bypassed. Actual figure pixels, reuse rights and
third-party credits remain unverified. No figures were downloaded or added to
the runtime. The article is a source lead, not accepted commercial evidence.

Next source step: acquire the full publisher text and original figures when
public access is available, inspect captions/credits and pixel anatomy, then
evaluate the proposal and candidate bindings. No registration, contact, access
request or external message has been sent.
